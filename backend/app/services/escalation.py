"""Escalation — the durable tick (Architecture.md §5).

In-memory timers die with serverless instances, so escalation is a pure
function of database state, driven every ~10 s by Cloud Scheduler hitting
/internal/escalation/tick (or the worker's local cron in dev):

    wave 1 at +30 s: radius ×2, re-rank, notify new candidates
    wave 2 at +45 s: radius ×3, re-rank, notify new candidates
    wave 3 at +60 s: prompt the victim to call 108/112 (timeline + push cue)
    expiry at +15 min: PENDING events with no acceptance → EXPIRED

Correctness comes from compare-and-set: each wave advances via a single
UPDATE ... WHERE escalation_wave = w-1 RETURNING, so overlapping ticks (or a
tick racing a deployment) can never double-notify a wave.
"""

import logging
import uuid

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants as c
from app.core.arq_pool import get_arq_pool
from app.models.sos import Response, SosEvent
from app.realtime import broadcast_safe
from app.services import sos_service
from app.services.geo import nearby_users
from app.services.notify import get_push_sender
from app.services.ranking import rank_candidates, top_n_for_severity

logger = logging.getLogger("nearhelp.escalation")


async def run_escalation_tick(session: AsyncSession) -> dict[str, int]:
    """One idempotent scanner pass. Safe to run concurrently."""
    summary = {"expired": 0, "wave1": 0, "wave2": 0, "wave3": 0}

    summary["expired"] += await _expire_stale_pending(session)

    for wave in (1, 2):
        advanced = await _advance_wave(session, wave)
        summary[f"wave{wave}"] = advanced
        if advanced:
            logger.info("escalated %s event(s) to wave %s", advanced, wave)

    summary["wave3"] = await _prompt_call_services(session)
    return summary


async def _expire_stale_pending(session: AsyncSession) -> int:
    cutoff = text(f"interval '{c.PENDING_EXPIRE_MINUTES} minutes'")
    result = await session.execute(
        update(SosEvent)
        .where(
            SosEvent.status == "pending",
            SosEvent.created_at < func.now() - cutoff,
        )
        .values(status="expired")
        .returning(SosEvent.id)
    )
    expired_ids = result.scalars().all()
    for sos_id in expired_ids:
        await sos_service.record_timeline(session, sos_id, c.EVENT_SOS_EXPIRED)
        broadcast_safe(sos_id, {"type": "sos_expired"})
    if expired_ids:
        await session.commit()
    return len(expired_ids)


async def _claim_wave(session: AsyncSession, sos_id: uuid.UUID, wave: int) -> bool:
    """CAS: only one concurrent tick moves an event from wave-1 to wave."""
    result = await session.execute(
        update(SosEvent)
        .where(SosEvent.id == sos_id, SosEvent.escalation_wave == wave - 1)
        .values(escalation_wave=wave, last_escalated_at=func.now())
        .returning(SosEvent.id)
    )
    claimed = result.scalar_one_or_none() is not None
    if claimed:
        await session.commit()
    return claimed


async def _advance_wave(session: AsyncSession, wave: int) -> int:
    """Expand the radius, notify newly-reachable responders. Returns # events."""
    threshold = text(f"interval '{c.WAVE_SECONDS[wave - 1]} seconds'")
    result = await session.execute(
        select(SosEvent).where(
            SosEvent.status == "pending",
            SosEvent.escalation_wave == wave - 1,
            SosEvent.created_at < func.now() - threshold,
        )
    )
    events = result.scalars().all()

    advanced = 0
    for event in events:
        if not await _claim_wave(session, event.id, wave):
            continue  # a concurrent tick already claimed it
        await session.refresh(event)

        multiplier = c.WAVE_RADIUS_MULTIPLIER[wave]
        new_radius = event.radius_m * multiplier
        already = set(
            (
                await session.scalars(
                    select(Response.responder_id).where(Response.sos_event_id == event.id)
                )
            ).all()
        )
        await _expand_and_notify(session, event, new_radius, wave, already)
        advanced += 1
    return advanced


async def _expand_and_notify(
    session: AsyncSession,
    event: SosEvent,
    new_radius: int,
    wave: int,
    already_notified: set[uuid.UUID],
) -> None:
    event.radius_m = new_radius
    lat, lon = await sos_service.event_lat_lon(session, event)

    candidates = await nearby_users(
        session,
        lat=lat,
        lon=lon,
        radius_m=new_radius,
        exclude_user_ids=already_notified | {event.broadcaster_id},
    )
    ranked = rank_candidates(
        candidates,
        crisis_type=event.crisis_type,
        radius_m=new_radius,
        top_n=top_n_for_severity(event.severity_score),
    )
    responder_ids = [r.candidate.user_id for r in ranked]
    for r in ranked:
        session.add(
            Response(sos_event_id=event.id, responder_id=r.candidate.user_id, status="notified")
        )

    await sos_service.record_timeline(
        session,
        event.id,
        c.EVENT_ESCALATION_WAVE,
        details={"wave": wave, "radius_m": new_radius, "notified": len(responder_ids)},
    )
    await session.commit()
    broadcast_safe(event.id, {"type": "escalation_wave", "wave": wave, "radius_m": new_radius})

    try:
        pool = await get_arq_pool()
        await pool.enqueue_job("fan_out_sos", str(event.id), wave, responder_ids)
    except Exception:
        logger.exception("escalation fan-out enqueue failed for sos %s wave %s", event.id, wave)


async def _prompt_call_services(session: AsyncSession) -> int:
    """Wave 3: no acceptance 60 s in — tell the victim to call 108/112.

    The backend only prompts (push cue + timeline); the human dials. Drill
    events never arm this prompt (improvements.md §2.2).
    """
    threshold = text(f"interval '{c.WAVE_SECONDS[2]} seconds'")
    result = await session.execute(
        update(SosEvent)
        .where(
            SosEvent.status == "pending",
            SosEvent.escalation_wave == 2,
            SosEvent.created_at < func.now() - threshold,
            SosEvent.is_drill.is_(False),
        )
        .values(escalation_wave=3, last_escalated_at=func.now())
        .returning(SosEvent.id)
    )
    event_ids = result.scalars().all()
    for sos_id in event_ids:
        await sos_service.record_timeline(
            session, sos_id, c.EVENT_CALL_SERVICES_PROMPTED, details={"numbers": ["108", "112"]}
        )
        broadcast_safe(sos_id, {"type": "call_services_prompt", "numbers": ["108", "112"]})
    if event_ids:
        await session.commit()

    # Push cue to the victim's own devices so the prompt surfaces off-app too.
    sender = get_push_sender()
    for sos_id in event_ids:
        event = await session.get(SosEvent, sos_id)
        if event is None:
            continue
        devices = await _broadcaster_tokens(session, event)
        if devices:
            await sender.send_tokens(
                devices, {"type": "call_services_prompt", "sos_id": str(event.id)}
            )
    return len(event_ids)


async def _broadcaster_tokens(session: AsyncSession, event: SosEvent) -> list[str]:
    from app.models.device import UserDevice

    rows = await session.scalars(
        select(UserDevice.fcm_token).where(UserDevice.user_id == event.broadcaster_id)
    )
    return list(rows)
