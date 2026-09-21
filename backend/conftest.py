"""
=============================================================================
CONFTEST.PY - Fixtures compartilhadas dos testes
=============================================================================

O pytest carrega este arquivo automaticamente antes de rodar os testes do
diretório `tests/`. Fixtures definidas aqui ficam disponíveis para qualquer
arquivo de teste, sem precisar de import.

POR QUE O RESET DE BANCO É NECESSÁRIO:
`database.py` guarda o estado em variáveis de módulo (`users_db` e
`user_id_counter`), não em um banco de dados de verdade. Isso significa que,
sem um reset, os dados criados em um teste "vazariam" para o teste seguinte
e a ordem de execução passaria a importar - o que é exatamente o que um bom
conjunto de testes unitários deve evitar.
=============================================================================
"""

import pytest
from fastapi.testclient import TestClient

import database as db
from main import app


@pytest.fixture(autouse=True)
def reset_database():
    """Garante que cada teste comece com o 'banco' em memória limpo."""
    db.users_db.clear()
    db.user_id_counter = 1
    yield
    db.users_db.clear()
    db.user_id_counter = 1


@pytest.fixture
def client():
    """TestClient do FastAPI: chama a aplicação em memória, sem subir um servidor real."""
    return TestClient(app)
