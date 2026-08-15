"""User profile endpoints (Phases 1-2).

All routes require a Bearer access token and sit behind the per-user rate
limit (100 req/min). FCM registration is multi-device: one row per
(user, device) pair; skill claims create pending verification rows with the
certificate stored via the storage service. Location updates feed the geo
query that makes a user discoverable as a nearby responder (Phase 2).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_with_rate_limit
from app.core.constants import SKILL_TYPES
from app.db.session import get_session
from app.models.device import UserDevice
from app.models.skills import SkillVerification
from app.models.user import User
from app.schemas.auth import UserOut
from app.schemas.user import (
    FcmTokenRequest,
    LocationUpdateRequest,
    SkillVerificationOut,
    UserUpdateRequest,
)
from app.services.geo import point
from app.services.storage import CertificateStorage, get_certificate_storage

router = APIRouter(prefix="/api/users", tags=["users"])


@router.put("/me/location", status_code=204)
async def update_location(
    body: LocationUpdateRequest,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Publish the user's location for responder discoverability.

    Privacy rule (Architecture.md §9): the retention job nulls this after
    events resolve / on opt-out; between events it is the price of being
    findable when someone nearby needs help.
    """
    user.location = point(body.lat, body.lon)
    await session.commit()


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(current_user_with_rate_limit)) -> UserOut:
    return UserOut.from_user(user)


@router.put("/me", response_model=UserOut)
async def update_me(
    body: UserUpdateRequest,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in changes.items():
        setattr(user, field, value)
    if changes:
        await session.commit()
        await session.refresh(user)
    return UserOut.from_user(user)


@router.post("/me/fcm-token", status_code=204)
async def register_fcm_token(
    body: FcmTokenRequest,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Upsert the (user, device) row — same device_id rotates its token."""
    device = await session.scalar(
        select(UserDevice).where(
            UserDevice.user_id == user.id, UserDevice.device_id == body.device_id
        )
    )
    if device is None:
        session.add(UserDevice(user_id=user.id, device_id=body.device_id, fcm_token=body.fcm_token))
    else:
        device.fcm_token = body.fcm_token
    await session.commit()


@router.post("/me/skills", response_model=SkillVerificationOut, status_code=201)
async def claim_skill(
    skill_type: str,
    certificate: UploadFile | None = None,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
    storage: CertificateStorage = Depends(get_certificate_storage),
) -> SkillVerificationOut:
    if skill_type not in SKILL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"unknown skill_type '{skill_type}' (allowed: {', '.join(SKILL_TYPES)})",
        )

    verification = SkillVerification(
        id=uuid.uuid4(), user_id=user.id, skill_type=skill_type, status="pending"
    )
    if certificate is not None and certificate.filename:
        data = await certificate.read()
        verification.certificate_path = storage.save(data, certificate.filename)
    session.add(verification)
    await session.commit()
    return SkillVerificationOut(
        id=verification.id,
        skill_type=verification.skill_type,
        status=verification.status,
        submitted_at=verification.created_at,
        has_certificate=verification.certificate_path is not None,
    )


@router.get("/me/skills", response_model=list[SkillVerificationOut])
async def list_my_skills(
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> list[SkillVerificationOut]:
    rows = await session.scalars(
        select(SkillVerification)
        .where(SkillVerification.user_id == user.id)
        .order_by(SkillVerification.created_at.desc())
    )
    return [
        SkillVerificationOut(
            id=row.id,
            skill_type=row.skill_type,
            status=row.status,
            submitted_at=row.created_at,
            has_certificate=row.certificate_path is not None,
        )
        for row in rows
    ]


@router.get("/me/skills/{verification_id}/certificate")
async def download_my_certificate(
    verification_id: uuid.UUID,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
    storage: CertificateStorage = Depends(get_certificate_storage),
) -> Response:
    """Owner-only certificate download (admin review access lands in Phase 6)."""
    verification = await session.get(SkillVerification, verification_id)
    if verification is None or verification.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="claim not found")
    if not verification.certificate_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no certificate on file")

    data, content_type = storage.open(verification.certificate_path)
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="certificate{verification_id}"'},
    )
