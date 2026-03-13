from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

__all__ = [
    "PatchBook",
    "IncomingBook",
    "ReturnedBook",
    "ReturnedAllBooks",
]


class BaseBook(BaseModel):
    title: str
    author: str
    year: int
    seller_id: int


class PatchBook(BaseModel):
    title: str | None = None
    author: str | None = None
    year: int | None = None
    pages: int | None = None
    seller_id: int | None = None


class IncomingBook(BaseBook):
    pages: int = Field(default=100, alias="count_pages")

    @field_validator("year")
    @staticmethod
    def validate_year(val: int):
        if val < 2020:
            raise PydanticCustomError("Validation error", "Year is too old!")

        return val


class ReturnedBook(BaseBook):
    id: int
    pages: int


class ReturnedAllBooks(BaseModel):
    books: list[ReturnedBook]
