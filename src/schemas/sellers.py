from pydantic import BaseModel

from .books import ReturnedBook

__all__ = [
    "IncomingSeller",
    "UpdatedSeller",
    "ReturnedSeller",
    "ReturnedSellerWithBooks",
    "ReturnedAllSellers",
]


class BaseSeller(BaseModel):
    first_name: str
    last_name: str
    e_mail: str


class IncomingSeller(BaseSeller):
    password: str


class UpdatedSeller(BaseSeller):
    pass


class ReturnedSeller(BaseSeller):
    id: int


class ReturnedSellerWithBooks(ReturnedSeller):
    books: list[ReturnedBook]


class ReturnedAllSellers(BaseModel):
    sellers: list[ReturnedSeller]
