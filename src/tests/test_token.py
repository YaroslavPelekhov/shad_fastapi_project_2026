import pytest
from fastapi import status

from src.models.sellers import Seller

API_V1_URL_PREFIX = "/api/v1/token"


@pytest.mark.asyncio()
async def test_create_token(db_session, async_client):
    seller = Seller(
        first_name="Ivan",
        last_name="Petrov",
        e_mail="ivan.petrov@mail.com",
        password="strong_password",
    )
    db_session.add(seller)
    await db_session.flush()

    response = await async_client.post(
        API_V1_URL_PREFIX,
        json={"email": "ivan.petrov@mail.com", "password": "strong_password"},
    )
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"
    assert isinstance(response_data["access_token"], str)
    assert len(response_data["access_token"]) > 10


@pytest.mark.asyncio()
async def test_create_token_with_invalid_credentials(db_session, async_client):
    seller = Seller(
        first_name="Ivan",
        last_name="Petrov",
        e_mail="ivan.petrov@mail.com",
        password="strong_password",
    )
    db_session.add(seller)
    await db_session.flush()

    response = await async_client.post(
        API_V1_URL_PREFIX,
        json={"email": "ivan.petrov@mail.com", "password": "wrong_password"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
