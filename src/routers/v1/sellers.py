from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.configurations.auth import get_current_seller
from src.configurations.database import get_async_session
from src.models.sellers import Seller
from src.schemas import (
    IncomingSeller,
    ReturnedAllSellers,
    ReturnedSeller,
    ReturnedSellerWithBooks,
    UpdatedSeller,
)
from src.services import SellerService

sellers_router = APIRouter(prefix="/seller", tags=["seller"])

DBSession = Annotated[AsyncSession, Depends(get_async_session)]
CurrentSeller = Annotated[Seller, Depends(get_current_seller)]


@sellers_router.post("", response_model=ReturnedSeller, status_code=status.HTTP_201_CREATED)
async def create_seller(seller: IncomingSeller, session: DBSession):
    new_seller = await SellerService(session).add_seller(seller)
    return new_seller


@sellers_router.get("", response_model=ReturnedAllSellers)
async def get_all_sellers(session: DBSession):
    sellers = await SellerService(session).get_all_sellers()
    return {"sellers": sellers}


@sellers_router.get("/{seller_id}", response_model=ReturnedSellerWithBooks)
async def get_single_seller(seller_id: int, session: DBSession, _: CurrentSeller):
    seller = await SellerService(session).get_single_seller(seller_id)
    if seller is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return seller


@sellers_router.put("/{seller_id}", response_model=ReturnedSeller)
async def update_seller(seller_id: int, seller_data: UpdatedSeller, session: DBSession):
    updated_seller = await SellerService(session).update_seller(seller_id, seller_data)
    if updated_seller is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return updated_seller


@sellers_router.delete("/{seller_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seller(seller_id: int, session: DBSession):
    deleted_seller = await SellerService(session).delete_seller(seller_id)
    if not deleted_seller:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
