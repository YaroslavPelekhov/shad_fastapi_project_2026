from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.database import get_async_session
from src.configurations.settings import settings
from src.models.sellers import Seller

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(payload: dict) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    token_payload = payload.copy()
    token_payload["exp"] = expires_at

    return jwt.encode(token_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_seller(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Seller:
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise auth_error

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError as exc:
        raise auth_error from exc

    subject = payload.get("sub")
    if subject is None:
        raise auth_error

    try:
        seller_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise auth_error from exc

    seller = await session.get(Seller, seller_id)
    if seller is None:
        raise auth_error

    return seller
