"""AI-facing endpoints (Phase 5).

POST /api/ai/classify      — classify free text (fallback ladder applies)
GET  /api/sos/{id}/guidance — RAG guidance for an event (participants only);
                              served from ai_outputs when already generated.
"""

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_with_rate_limit
from app.db.session import get_session
from app.models.ai_output import AiOutput
from app.models.sos import SosEvent
from app.models.user import User
from app.services import ai, sos_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=3, max_length=2000)


class ClassificationOut(BaseModel):
    emergency_type: str
    sub_type: str | None
    severity_score: int
    confidence: float
    recommended_radius_km: float
    suggested_responder_skills: list[str]
    source: str
    latency_ms: int


@router.post("/classify", response_model=ClassificationOut)
async def classify(
    body: ClassifyRequest,
    user: User = Depends(current_user_with_rate_limit),
) -> ClassificationOut:
    result = await ai.classify_emergency(body.text)
    return ClassificationOut(**result.as_payload(), latency_ms=result.latency_ms)


async def load_guidance_output(session: AsyncSession, sos_id: uuid.UUID) -> AiOutput | None:
    return await session.scalar(
        select(AiOutput)
        .where(AiOutput.sos_event_id == sos_id, AiOutput.kind == "guidance")
        .order_by(AiOutput.created_at.desc())
        .limit(1)
    )


async def get_event_for_participant(
    session: AsyncSession, sos_id: uuid.UUID, user: User
) -> SosEvent:
    event = await session.get(SosEvent, sos_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event not found")
    if event.broadcaster_id == user.id:
        return event
    if await sos_service.get_participation(session, event, user.id) is not None:
        return event
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event not found")


class GuidanceOut(BaseModel):
    sos_id: uuid.UUID
    mode: str
    steps: list[dict]
    summary: str
    retrieved_refs: list[dict]
    prompt_version: str | None
    latency_ms: int
    disclaimer: str


DISCLAIMER = (
    "This guidance is based on published first-aid protocols and is NOT a "
    "substitute for professional medical advice, diagnosis, or treatment. "
    "Always call emergency services (108/112) for serious emergencies."
)


async def guidance_for_event(session: AsyncSession, event: SosEvent) -> GuidanceOut:
    """Served-cached copy first; generate (ladder) when the job hasn't run."""
    cached = await load_guidance_output(session, event.id)
    if cached is not None:
        payload = cached.payload
        return GuidanceOut(
            sos_id=event.id,
            mode=payload.get("mode", "unknown"),
            steps=payload.get("steps", []),
            summary=payload.get("summary", ""),
            retrieved_refs=payload.get("retrieved_refs", []),
            prompt_version=cached.prompt_version,
            latency_ms=cached.latency_ms,
            disclaimer=DISCLAIMER,
        )

    started = time.perf_counter()
    guidance = await ai.generate_guidance(
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
    await session.commit()
    return GuidanceOut(
        sos_id=event.id,
        mode=guidance.mode,
        steps=guidance.steps,
        summary=guidance.summary,
        retrieved_refs=guidance.retrieved_refs,
        prompt_version=guidance.prompt_version,
        latency_ms=int((time.perf_counter() - started) * 1000),
        disclaimer=DISCLAIMER,
    )


def register_sos_guidance_route(sos_router: APIRouter) -> None:
    """Attaches GET /{sos_id}/guidance to the SOS router (shared loader)."""

    @sos_router.get("/{sos_id}/guidance", response_model=GuidanceOut)
    async def sos_guidance(
        sos_id: uuid.UUID,
        user: User = Depends(current_user_with_rate_limit),
        session: AsyncSession = Depends(get_session),
    ) -> GuidanceOut:
        event = await get_event_for_participant(session, sos_id, user)
        return await guidance_for_event(session, event)
