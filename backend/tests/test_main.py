import pytest
from fastapi import HTTPException

import database as db
from models import UserCreate
from routers.users import (
    get_users,
    get_user,
    create_user,
    update_user,
    delete_user,
)


@pytest.fixture(autouse=True)
def reset_database():
    """
    Limpa o banco em memória antes de cada teste.
    """
    db.users_db.clear()
    db.user_id_counter = 1


# ============================================================
# GET /users
# ============================================================

def test_get_users_empty_database():
    result = get_users()

    assert result == []


def test_get_users_returns_all_users():
    db.users_db[1] = {
        "id": 1,
        "name": "João",
        "email": "joao@email.com"
    }

    db.users_db[2] = {
        "id": 2,
        "name": "Maria",
        "email": "maria@email.com"
    }

    result = get_users()

    assert len(result) == 2
    assert result[0]["name"] == "João"
    assert result[1]["name"] == "Maria"


# ============================================================
# GET /users/{user_id}
# ============================================================

def test_get_user_existing():
    db.users_db[1] = {
        "id": 1,
        "name": "João",
        "email": "joao@email.com"
    }

    result = get_user(1)

    assert result["id"] == 1
    assert result["name"] == "João"
    assert result["email"] == "joao@email.com"


def test_get_user_not_found():
    with pytest.raises(HTTPException) as exc_info:
        get_user(999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


# ============================================================
# POST /users
# ============================================================

def test_create_user():
    user = UserCreate(
        name="João",
        email="joao@email.com"
    )

    result = create_user(user)

    assert result["id"] == 1
    assert result["name"] == "João"
    assert result["email"] == "joao@email.com"

    assert 1 in db.users_db


def test_create_user_increments_id():
    user1 = UserCreate(
        name="João",
        email="joao@email.com"
    )

    user2 = UserCreate(
        name="Maria",
        email="maria@email.com"
    )

    result1 = create_user(user1)
    result2 = create_user(user2)

    assert result1["id"] == 1
    assert result2["id"] == 2

    assert len(db.users_db) == 2


# ============================================================
# PUT /users/{user_id}
# ============================================================

def test_update_user():
    db.users_db[1] = {
        "id": 1,
        "name": "João",
        "email": "joao@email.com"
    }

    updated_user = UserCreate(
        name="João Silva",
        email="joao.silva@email.com"
    )

    result = update_user(1, updated_user)

    assert result["id"] == 1
    assert result["name"] == "João Silva"
    assert result["email"] == "joao.silva@email.com"


def test_update_user_not_found():
    user = UserCreate(
        name="João",
        email="joao@email.com"
    )

    with pytest.raises(HTTPException) as exc_info:
        update_user(999, user)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


# ============================================================
# DELETE /users/{user_id}
# ============================================================

def test_delete_user():
    db.users_db[1] = {
        "id": 1,
        "name": "João",
        "email": "joao@email.com"
    }

    delete_user(1)

    assert 1 not in db.users_db


def test_delete_user_not_found():
    with pytest.raises(HTTPException) as exc_info:
        delete_user(999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"