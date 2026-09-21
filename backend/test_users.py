"""
=============================================================================
TEST_USERS.PY - Testes unitários das rotas de usuários (routers/users.py)
=============================================================================

Cobre as 5 operações expostas em /api/users:

    GET    /api/users/          -> listar usuários
    GET    /api/users/{id}      -> buscar um usuário
    POST   /api/users/          -> criar usuário
    PUT    /api/users/{id}      -> atualizar usuário
    DELETE /api/users/{id}      -> remover usuário

Os testes usam o TestClient do FastAPI (baseado em httpx), que invoca a
aplicação diretamente em memória - sem precisar subir um servidor real nem
fazer chamadas de rede. O fixture `client` e o reset automático do banco
em memória vêm de conftest.py.
=============================================================================
"""

VALID_USER = {"name": "Ana Souza", "email": "ana.souza@example.com"}
OTHER_USER = {"name": "Bruno Lima", "email": "bruno.lima@example.com"}


def create_user(client, payload=None):
    """Helper: cria um usuário via API e devolve o corpo já em JSON."""
    response = client.post("/api/users/", json=payload or VALID_USER)
    assert response.status_code == 201
    return response.json()


# -----------------------------------------------------------------------
# GET /api/users/ - listar usuários
# -----------------------------------------------------------------------


def test_list_users_empty(client):
    response = client.get("/api/users/")

    assert response.status_code == 200
    assert response.json() == []


def test_list_users_returns_created_users(client):
    user1 = create_user(client, VALID_USER)
    user2 = create_user(client, OTHER_USER)

    response = client.get("/api/users/")

    assert response.status_code == 200
    assert response.json() == [user1, user2]


def test_list_users_without_trailing_slash_redirects(client):
    # A rota é declarada como "/" dentro do router (prefix="/api/users"),
    # então o caminho "oficial" é /api/users/. Sem a barra final, o
    # FastAPI devolve um redirect 307 para a URL com barra.
    response = client.get("/api/users", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].endswith("/api/users/")


# -----------------------------------------------------------------------
# GET /api/users/{user_id} - buscar um usuário
# -----------------------------------------------------------------------


def test_get_user_existing(client):
    created = create_user(client)

    response = client.get(f"/api/users/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_user_not_found(client):
    response = client.get("/api/users/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_get_user_invalid_id_type(client):
    # user_id é tipado como int na rota; um valor não numérico deve falhar
    # na validação do FastAPI antes de chegar na lógica da rota.
    response = client.get("/api/users/not-an-id")

    assert response.status_code == 422


# -----------------------------------------------------------------------
# POST /api/users/ - criar usuário
# -----------------------------------------------------------------------


def test_create_user_success(client):
    response = client.post("/api/users/", json=VALID_USER)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == VALID_USER["name"]
    assert body["email"] == VALID_USER["email"]
    assert body["id"] == 1


def test_create_user_persists_in_list(client):
    create_user(client)

    response = client.get("/api/users/")

    assert len(response.json()) == 1


def test_create_user_assigns_incrementing_ids(client):
    first = create_user(client, VALID_USER)
    second = create_user(client, OTHER_USER)

    assert first["id"] == 1
    assert second["id"] == 2


def test_create_user_ids_are_not_reused_after_delete(client):
    first = create_user(client, VALID_USER)
    client.delete(f"/api/users/{first['id']}")

    second = create_user(client, OTHER_USER)

    # O contador global segue avançando mesmo depois de uma remoção.
    assert second["id"] == 2


def test_create_user_invalid_email(client):
    response = client.post("/api/users/", json={"name": "Carla", "email": "email-invalido"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "email"]


def test_create_user_missing_required_field(client):
    response = client.post("/api/users/", json={"name": "Diego"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "email"]


def test_create_user_ignores_client_supplied_id(client):
    # UserCreate não tem campo "id"; um id enviado pelo cliente é
    # descartado, e o servidor continua responsável por gerar o próprio id.
    response = client.post("/api/users/", json={"id": 999, **VALID_USER})

    assert response.status_code == 201
    assert response.json()["id"] == 1


# -----------------------------------------------------------------------
# PUT /api/users/{user_id} - atualizar usuário
# -----------------------------------------------------------------------


def test_update_user_success(client):
    created = create_user(client)
    updated_payload = {"name": "Ana Souza Silva", "email": "ana.silva@example.com"}

    response = client.put(f"/api/users/{created['id']}", json=updated_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == updated_payload["name"]
    assert body["email"] == updated_payload["email"]
    assert body["id"] == created["id"]


def test_update_user_persists_change(client):
    created = create_user(client)
    updated_payload = {"name": "Novo Nome", "email": "novo@example.com"}
    client.put(f"/api/users/{created['id']}", json=updated_payload)

    response = client.get(f"/api/users/{created['id']}")

    assert response.json()["name"] == "Novo Nome"


def test_update_user_not_found(client):
    response = client.put("/api/users/999", json=VALID_USER)

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_update_user_invalid_email(client):
    created = create_user(client)

    response = client.put(f"/api/users/{created['id']}", json={"name": "X", "email": "invalido"})

    assert response.status_code == 422


# -----------------------------------------------------------------------
# DELETE /api/users/{user_id} - remover usuário
# -----------------------------------------------------------------------


def test_delete_user_success(client):
    created = create_user(client)

    response = client.delete(f"/api/users/{created['id']}")

    assert response.status_code == 204
    assert response.text == ""


def test_delete_user_removes_from_list(client):
    created = create_user(client)
    client.delete(f"/api/users/{created['id']}")

    response = client.get("/api/users/")

    assert response.json() == []


def test_delete_user_not_found(client):
    response = client.delete("/api/users/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}


def test_delete_user_twice_returns_404_second_time(client):
    created = create_user(client)
    client.delete(f"/api/users/{created['id']}")

    response = client.delete(f"/api/users/{created['id']}")

    assert response.status_code == 404
