import pytest
from fastapi import status
from sqlalchemy import select

from src.models.books import Book
from src.models.sellers import Seller

API_V1_URL_PREFIX = "/api/v1/seller"


async def _get_auth_headers(async_client, seller: Seller) -> dict[str, str]:
    response = await async_client.post(
        "/api/v1/token",
        json={"email": seller.e_mail, "password": seller.password},
    )
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio()
async def test_create_seller(async_client):
    data = {
        "first_name": "Ivan",
        "last_name": "Petrov",
        "e_mail": "ivan.petrov@mail.com",
        "password": "strong_password",
    }
    response = await async_client.post(API_V1_URL_PREFIX, json=data)

    assert response.status_code == status.HTTP_201_CREATED

    response_data = response.json()
    assert response_data["first_name"] == data["first_name"]
    assert response_data["last_name"] == data["last_name"]
    assert response_data["e_mail"] == data["e_mail"]
    assert "id" in response_data
    assert "password" not in response_data


@pytest.mark.asyncio()
async def test_get_all_sellers(db_session, async_client):
    seller_1 = Seller(first_name="Ivan", last_name="Petrov", e_mail="ivan@mail.com", password="pass_1")
    seller_2 = Seller(first_name="Petr", last_name="Ivanov", e_mail="petr@mail.com", password="pass_2")
    db_session.add_all([seller_1, seller_2])
    await db_session.flush()

    response = await async_client.get(API_V1_URL_PREFIX)
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert len(response_data["sellers"]) == 2
    assert response_data == {
        "sellers": [
            {
                "id": seller_1.id,
                "first_name": "Ivan",
                "last_name": "Petrov",
                "e_mail": "ivan@mail.com",
            },
            {
                "id": seller_2.id,
                "first_name": "Petr",
                "last_name": "Ivanov",
                "e_mail": "petr@mail.com",
            },
        ]
    }
    assert all("password" not in seller for seller in response_data["sellers"])


@pytest.mark.asyncio()
async def test_get_single_seller_with_books(db_session, async_client):
    seller = Seller(first_name="Ivan", last_name="Petrov", e_mail="ivan@mail.com", password="pass_1")
    db_session.add(seller)
    await db_session.flush()

    auth_headers = await _get_auth_headers(async_client, seller)

    book_1 = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2021,
        pages=104,
        seller_id=seller.id,
    )
    book_2 = Book(
        author="Lermontov",
        title="Mtziri",
        year=2022,
        pages=150,
        seller_id=seller.id,
    )
    db_session.add_all([book_1, book_2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/{seller.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data == {
        "id": seller.id,
        "first_name": "Ivan",
        "last_name": "Petrov",
        "e_mail": "ivan@mail.com",
        "books": [
            {
                "id": book_1.id,
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2021,
                "pages": 104,
                "seller_id": seller.id,
            },
            {
                "id": book_2.id,
                "title": "Mtziri",
                "author": "Lermontov",
                "year": 2022,
                "pages": 150,
                "seller_id": seller.id,
            },
        ],
    }
    assert "password" not in response_data


@pytest.mark.asyncio()
async def test_get_single_seller_without_token(db_session, async_client):
    seller = Seller(first_name="Ivan", last_name="Petrov", e_mail="ivan@mail.com", password="pass_1")
    db_session.add(seller)
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/{seller.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
async def test_get_single_seller_with_invalid_id(db_session, async_client):
    seller = Seller(first_name="Ivan", last_name="Petrov", e_mail="ivan@mail.com", password="pass_1")
    db_session.add(seller)
    await db_session.flush()

    auth_headers = await _get_auth_headers(async_client, seller)

    response = await async_client.get(f"{API_V1_URL_PREFIX}/999999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_update_seller(db_session, async_client):
    seller = Seller(first_name="Ivan", last_name="Petrov", e_mail="ivan@mail.com", password="pass_1")
    db_session.add(seller)
    await db_session.flush()

    data = {
        "first_name": "Sergey",
        "last_name": "Sidorov",
        "e_mail": "sergey@mail.com",
    }
    response = await async_client.put(f"{API_V1_URL_PREFIX}/{seller.id}", json=data)
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data == {
        "id": seller.id,
        "first_name": "Sergey",
        "last_name": "Sidorov",
        "e_mail": "sergey@mail.com",
    }
    assert "password" not in response_data

    updated_seller = await db_session.get(Seller, seller.id)
    assert updated_seller.password == "pass_1"


@pytest.mark.asyncio()
async def test_delete_seller_cascades_books(db_session, async_client):
    seller = Seller(first_name="Ivan", last_name="Petrov", e_mail="ivan@mail.com", password="pass_1")
    db_session.add(seller)
    await db_session.flush()

    book_1 = Book(author="Pushkin", title="Eugeny Onegin", year=2021, pages=104, seller_id=seller.id)
    book_2 = Book(author="Lermontov", title="Mtziri", year=2022, pages=150, seller_id=seller.id)
    db_session.add_all([book_1, book_2])
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{seller.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()
    seller_in_db = await db_session.scalar(select(Seller).where(Seller.id == seller.id))
    assert seller_in_db is None

    all_books = await db_session.execute(select(Book))
    books = all_books.scalars().all()
    assert len(books) == 0


@pytest.mark.asyncio()
async def test_delete_seller_with_invalid_seller_id(db_session, async_client):
    seller = Seller(first_name="Ivan", last_name="Petrov", e_mail="ivan@mail.com", password="pass_1")
    db_session.add(seller)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{seller.id + 1}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
