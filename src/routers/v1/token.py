from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.auth import create_access_token
from src.configurations.database import get_async_session
from src.schemas import TokenRequest, TokenResponse
from src.services import SellerService

token_router = APIRouter(tags=["token"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


@token_router.post("/token", response_model=TokenResponse)
async def get_token(credentials: TokenRequest, session: DBSession):
    seller = await SellerService(session).get_seller_by_credentials(credentials.email, credentials.password)
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": str(seller.id), "email": seller.e_mail})

    return {"access_token": access_token, "token_type": "bearer"}
