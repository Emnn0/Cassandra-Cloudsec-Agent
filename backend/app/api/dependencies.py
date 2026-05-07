"""FastAPI dependency injection: DB session + Clerk JWT auth."""
from __future__ import annotations

import logging
from typing import Annotated

import httpx
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import User
from app.db.session import get_db

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# DB dependency (re-exported for convenience)
# ---------------------------------------------------------------------------

DBDep = Annotated[AsyncSession, Depends(get_db)]


# ---------------------------------------------------------------------------
# Clerk JWT verification
# ---------------------------------------------------------------------------

async def _verify_clerk_token(authorization: str) -> dict:
    """Call Clerk's /oauth/token/info to validate the Bearer token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.clerk.com/v1/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Clerk token.",
        )
    return resp.json()


async def get_current_user(
    db: DBDep,
    authorization: Annotated[str, Header()] = "",
) -> User:
    """Validate Clerk JWT and return (or create) the corresponding User row.

    Dev bypass: when CLERK_SECRET_KEY is empty the endpoint runs without auth
    and returns (or creates) a synthetic dev user so the full pipeline can be
    exercised locally without a Clerk account.
    """
    clerk_configured = bool(settings.clerk_secret_key)

    # ── Dev bypass ────────────────────────────────────────────────────────────
    if not clerk_configured:
        dev_clerk_id = "dev_local_user"
        result = await db.execute(select(User).where(User.clerk_id == dev_clerk_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(clerk_id=dev_clerk_id, email="dev@localhost")
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info("Dev mode: created synthetic user clerk_id=%s", dev_clerk_id)
        return user

    # ── Production: require Authorization header ───────────────────────────
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing.",
        )

    clerk_data = await _verify_clerk_token(authorization)
    clerk_id: str = clerk_data.get("id", "")
    email: str = (
        clerk_data.get("email_addresses", [{}])[0].get("email_address", "") or ""
    )

    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(clerk_id=clerk_id, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("New user created: clerk_id=%s", clerk_id)

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]