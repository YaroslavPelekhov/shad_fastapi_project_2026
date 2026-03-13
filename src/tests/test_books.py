import pytest
from fastapi import status
from sqlalchemy import select

from src.models.books import Book
from src.models.sellers import Seller

API_V1_URL_PREFIX = "/api/v1/books"


async def _create_seller(db_session, idx: int = 1) -> Seller:
    seller = Seller(
        first_name=f"Name{idx}",
        last_name=f"Surname{idx}",
        e_mail=f"seller{idx}@mail.com",
        password="secure_password",
    )
    db_session.add(seller)
    await db_session.flush()
    return seller


async def _get_auth_headers(async_client, seller: Seller) -> dict[str, str]:
    response = await async_client.post(
        "/api/v1/token",
        json={"email": seller.e_mail, "password": seller.password},
    )
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio()
async def test_create_book(db_session, async_client):
    seller = await _create_seller(db_session)
    auth_headers = await _get_auth_headers(async_client, seller)
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": seller.id,
    }
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data, headers=auth_headers)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()
    resp_book_id = result_data.pop("id", None)
    assert resp_book_id is not None, "Book id not returned from endpoint"

    assert result_data == {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "pages": 300,
        "year": 2025,
        "seller_id": seller.id,
    }


@pytest.mark.asyncio()
async def test_create_book_without_token(db_session, async_client):
    seller = await _create_seller(db_session)
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": seller.id,
    }
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
async def test_create_book_with_old_year(db_session, async_client):
    seller = await _create_seller(db_session)
    auth_headers = await _get_auth_headers(async_client, seller)
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 1986,
        "seller_id": seller.id,
    }
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data, headers=auth_headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio()
async def test_create_book_with_invalid_seller_id(db_session, async_client):
    seller = await _create_seller(db_session)
    auth_headers = await _get_auth_headers(async_client, seller)
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": 999999,
    }
    response = await async_client.post(f"{API_V1_URL_PREFIX}/", json=data, headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_get_books(db_session, async_client):
    seller = await _create_seller(db_session)
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2021, pages=104, seller_id=seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=2021, pages=108, seller_id=seller.id)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["books"]) == 2

    assert response.json() == {
        "books": [
            {
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2021,
                "id": book.id,
                "pages": 104,
                "seller_id": seller.id,
            },
            {
                "title": "Mziri",
                "author": "Lermontov",
                "year": 2021,
                "id": book_2.id,
                "pages": 108,
                "seller_id": seller.id,
            },
        ]
    }


@pytest.mark.asyncio()
async def test_get_single_book(db_session, async_client):
    seller = await _create_seller(db_session)
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)
    book_2 = Book(author="Lermontov", title="Mziri", year=1997, pages=104, seller_id=seller.id)

    db_session.add_all([book, book_2])
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/{book.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "year": 2001,
        "pages": 104,
        "id": book.id,
        "seller_id": seller.id,
    }


@pytest.mark.asyncio()
async def test_get_single_book_with_wrong_id(db_session, async_client):
    seller = await _create_seller(db_session)
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.get(f"{API_V1_URL_PREFIX}/426548")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_update_book(db_session, async_client):
    seller_1 = await _create_seller(db_session, idx=1)
    seller_2 = await _create_seller(db_session, idx=2)
    auth_headers = await _get_auth_headers(async_client, seller_1)
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller_1.id)

    db_session.add(book)
    await db_session.flush()

    data = {
        "title": "Mziri",
        "author": "Lermontov",
        "pages": 250,
        "year": 2024,
        "id": book.id,
        "seller_id": seller_2.id,
    }

    response = await async_client.put(
        f"{API_V1_URL_PREFIX}/{book.id}",
        json=data,
        headers=auth_headers,
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    res = await db_session.get(Book, book.id)
    assert res.title == "Mziri"
    assert res.author == "Lermontov"
    assert res.pages == 250
    assert res.year == 2024
    assert res.id == book.id
    assert res.seller_id == seller_2.id


@pytest.mark.asyncio()
async def test_update_book_without_token(db_session, async_client):
    seller = await _create_seller(db_session, idx=1)
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    data = {
        "title": "Mziri",
        "author": "Lermontov",
        "pages": 250,
        "year": 2024,
        "id": book.id,
        "seller_id": seller.id,
    }

    response = await async_client.put(
        f"{API_V1_URL_PREFIX}/{book.id}",
        json=data,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio()
async def test_patch_book(db_session, async_client):
    seller = await _create_seller(db_session)
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2025, pages=104, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    patch_data = {
        "title": "Patched Title",
        "pages": 250,
    }

    response = await async_client.patch(
        f"{API_V1_URL_PREFIX}/{book.id}",
        json=patch_data,
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["title"] == "Patched Title"
    assert response_data["pages"] == 250
    assert response_data["author"] == "Pushkin"
    assert response_data["year"] == 2025
    assert response_data["seller_id"] == seller.id


@pytest.mark.asyncio()
async def test_patch_book_with_invalid_book_id(async_client):
    patch_data = {
        "title": "Patched Title",
    }

    response = await async_client.patch(
        f"{API_V1_URL_PREFIX}/999999",
        json=patch_data,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio()
async def test_delete_book(db_session, async_client):
    seller = await _create_seller(db_session)
    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{book.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    await db_session.flush()
    all_books = await db_session.execute(select(Book))
    res = all_books.scalars().all()

    assert len(res) == 0


@pytest.mark.asyncio()
async def test_delete_book_with_invalid_book_id(db_session, async_client):
    seller = await _create_seller(db_session)
    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)

    db_session.add(book)
    await db_session.flush()

    response = await async_client.delete(f"{API_V1_URL_PREFIX}/{book.id + 1}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
