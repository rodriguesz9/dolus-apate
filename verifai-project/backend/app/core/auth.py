"""
Auth helpers:
  - get_current_user FastAPI dependency
  - Google ID-token verification
  - Daily usage limit check (plan middleware)
"""

import os
from datetime import datetime, timezone, date

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.history import VerificationLog

_bearer = HTTPBearer(auto_error=True)
_GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

DAILY_LIMITS = {
    "FREE":       3,
    "PRO":      100,
    "ENTERPRISE": 9999,
}


# ── Current user dependency ───────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise cred_exc
        user_id: str = payload.get("sub")
        if not user_id:
            raise cred_exc
    except JWTError:
        raise cred_exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise cred_exc
    return user


# ── Optional user (unauthenticated requests allowed) ─────────────────────────

_optional_bearer = HTTPBearer(auto_error=False)

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except Exception:
        return None


# ── Daily usage check ─────────────────────────────────────────────────────────

async def check_daily_limit(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)

    count_result = await db.execute(
        select(func.count(VerificationLog.id)).where(
            VerificationLog.user_id == user.id,
            VerificationLog.created_at >= today_start,
        )
    )
    daily_count = count_result.scalar_one()
    limit = DAILY_LIMITS.get(user.plan.value, 3)

    if daily_count >= limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "limite_diario",
                "message": f"Limite diário de {limit} análises atingido. Faça upgrade para o plano PRO!",
                "used": daily_count,
                "limit": limit,
                "plan": user.plan.value,
            },
        )
    return user


# ── Google OAuth ID-token verification ───────────────────────────────────────

def verify_google_id_token(token: str) -> dict:
    """
    Verifies a Google ID token returned by the frontend.
    Returns the decoded payload (sub, email, name, picture).
    Raises HTTPException on failure.
    """
    try:
        idinfo = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            _GOOGLE_CLIENT_ID,
        )
        return idinfo
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token Google inválido: {str(e)[:80]}",
        )
