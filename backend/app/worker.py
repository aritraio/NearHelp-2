"""arq worker — background jobs + the local escalation tick.

Run with: `arq app.worker.WorkerSettings` (the compose `worker` service).
Jobs:
  - fan_out_sos: chunked FCM sends to a wave's responders, delivery metrics
    into the timeline, UNREGISTERED token cleanup.
  - ai_pipeline: classify + severity (parallel to alerts), then RAG guidance,
    persisted to ai_outputs, broadcast + pushed as "guidance ready".
Cron:
  - escalation tick every 10 s (the dev stand-in for Cloud Scheduler; the
    /internal/escalation/tick endpoint drives it in the cloud deployment).
"""

import logging
import os
from datetime import UTC, datetime
from uuid import UUID

from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select

from app.core import constants as c
from app.db.session import get_session_factory
from app.models.ai_output import AiOutput
from app.models.sos import Response, SosEvent
from app.services import escalation as escalation_service
from app.services import sos_service
from app.services.ai import classify_emergency, generate_guidance
from app.services.ai.classify import severity_radius
from app.services.notify import (
    devices_for_responders,
    get_push_sender,
    prune_unregistered,
    sos_alert_payload,
)

logger = logging.getLogger("nearhelp.worker")


async def startup(ctx: dict) -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("worker started")


async def shutdown(ctx: dict) -> None:
    logger.info("worker stopped")


async def ping(ctx: dict) -> str:
    """Smoke-test task — proves the worker is reachable through Redis."""
    return "pong"


async def fan_out_sos(ctx: dict, sos_id: str, wave: int, responder_ids: list[str]) -> dict:
    """Send SOS pushes for one wave; record honest delivery metrics.

    Called by the API (initial wave) and by the escalation tick (waves 1-2).
    """
    started = datetime.now(UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        event = await session.get(SosEvent, UUID(sos_id))
        if event is None:
            logger.error("fan_out for missing sos %s", sos_id)
            return {"error": "missing"}

        lat, lon = await sos_service.event_lat_lon(session, event)
        payload = sos_alert_payload(
            sos_id=event.id,
            crisis_type=event.crisis_type,
            severity=event.severity_score,
            is_drill=event.is_drill,
            lat=lat,
            lon=lon,
        )
        if event.is_drill:
            payload["drill_banner"] = "DRILL — NOT A REAL EMERGENCY"

        sender = get_push_sender()
        devices = await devices_for_responders(session, [UUID(r) for r in responder_ids])
        tokens = [token for ts in devices.values() for token in ts]
        sent = failed = pruned = 0
        unregistered_all: list[str] = []
        for i in range(0, len(tokens), 50):
            chunk = tokens[i : i + 50]
            result = await sender.send_tokens(chunk, payload)
            sent += result["success"]
            failed += result["failure"]
            unregistered_all.extend(result["unregistered"])
        pruned = await prune_unregistered(session, unregistered_all)
        if pruned:
            logger.info("pruned %s unregistered device tokens", pruned)

        latency_ms = int((datetime.now(UTC) - started).total_seconds() * 1000)
        await sos_service.record_timeline(
            session,
            event.id,
            c.EVENT_RESPONDERS_NOTIFIED,
            details={
                "wave": wave,
                "pushed": True,
                "responders": len(responder_ids),
                "devices": len(tokens),
                "sent": sent,
                "failed": failed,
                "tokens_pruned": pruned,
                "fanout_ms": latency_ms,
            },
        )
        await session.commit()
        return {"sent": sent, "failed": failed, "pruned": pruned}


async def escalation_tick_cron(ctx: dict) -> dict:
    """Every 10 s: expire stale PENDING events and advance escalation waves."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        summary = await escalation_service.run_escalation_tick(session)
    if any(summary.values()):
        logger.info("escalation tick: %s", summary)
    return summary


async def ai_pipeline(ctx: dict, sos_id: str) -> dict:
    """The parallel AI path (Architecture.md §1): classify → severity →
    radius → RAG guidance → ai_outputs → timeline + WS broadcast + push cue.

    Runs entirely off the critical path; every step has a fallback so this
    job can never block or crash the alerting that already happened.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        event = await session.get(SosEvent, UUID(sos_id))
        if event is None:
            return {"error": "missing"}

        # --- Classification + severity (Gemini → heuristic ladder) ----------
        description = event.description or event.crisis_type or "emergency"
        classification = await classify_emergency(description)
        session.add(
            AiOutput(
                sos_event_id=event.id,
                kind="classification",
                mode=classification.source,
                prompt_version=classification.prompt_version,
                payload=classification.as_payload(),
                latency_ms=classification.latency_ms,
            )
        )
        if event.crisis_type is None or event.crisis_type == "other":
            event.crisis_type = classification.emergency_type
        event.sub_type = classification.sub_type
        event.severity_score = classification.severity_score
        event.radius_m = max(event.radius_m, severity_radius(classification.severity_score))
        await sos_service.record_timeline(
            session,
            event.id,
            c.EVENT_AI_CLASSIFIED,
            details={
                "source": classification.source,
                "crisis_type": event.crisis_type,
                "severity": classification.severity_score,
                "latency_ms": classification.latency_ms,
            },
        )
        await session.commit()

        # --- Guidance (RAG ladder) --------------------------------------------
        guidance = await generate_guidance(
            session, crisis_type=event.crisis_type, description=event.description
        )
        session.add(
            AiOutput(
                sos_event_id=event.id,
                kind="guidance",
                mode=guidance.mode,
                prompt_version=guidance.prompt_version,
                payload=guidance.as_payload(),
                retrieved_refs=guidance.retrieved_refs,
                latency_ms=guidance.latency_ms,
            )
        )
        await sos_service.record_timeline(
            session,
            event.id,
            c.EVENT_AI_GUIDANCE_READY,
            details={
                "mode": guidance.mode,
                "steps": len(guidance.steps),
                "latency_ms": guidance.latency_ms,
            },
        )

        # Push cue to notified responders' devices ("guidance ready").
        responder_ids = list(
            (
                await session.scalars(
                    select(Response.responder_id).where(Response.sos_event_id == event.id)
                )
            ).all()
        )
        devices = await devices_for_responders(session, responder_ids)
        tokens = [token for ts in devices.values() for token in ts]
        await session.commit()

    from app.realtime import broadcast_safe

    broadcast_safe(
        UUID(sos_id),
        {"type": "ai_guidance", "mode": guidance.mode, "steps": len(guidance.steps)},
    )
    if tokens:
        try:
            await get_push_sender().send_tokens(
                tokens, {"type": "guidance_ready", "sos_id": sos_id}
            )
        except Exception:
            logger.exception("guidance-ready push failed for sos %s", sos_id)

    return {
        "classification": classification.source,
        "guidance_mode": guidance.mode,
        "latency_ms": classification.latency_ms + guidance.latency_ms,
    }


class WorkerSettings:
    """arq entrypoint class (convention: settings as class attributes)."""

    functions = [ping, fan_out_sos, ai_pipeline]
    cron_jobs = [cron(escalation_tick_cron, second={0, 10, 20, 30, 40, 50}, unique=True)]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    job_timeout = 120
    max_jobs = 10
