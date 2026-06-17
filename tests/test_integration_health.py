"""Teste de integracao do endpoint GET /health.

Exercita a rota real da aplicacao (FastAPI + dependency injection +
serializacao) via TestClient. A unica dependencia externa — a conexao
com o Azure SQL — e substituida por um stub, entao o teste roda em
qualquer ambiente (CI/local) sem credenciais e valida que a API
responde com sucesso.
"""
from fastapi.testclient import TestClient

from main import app
from db import get_db


class _FakeCursor:
    """Cursor minimo: aceita .execute(...) e nao faz nada."""

    def execute(self, *args, **kwargs):
        return self


class _FakeConnection:
    """Conexao falsa que devolve um cursor stub (cobre conn.cursor().execute)."""

    def cursor(self):
        return _FakeCursor()


def _fake_get_db():
    yield _FakeConnection()


# Substitui a conexao real com o Azure SQL pelo stub
app.dependency_overrides[get_db] = _fake_get_db

client = TestClient(app)


def test_health_responde_com_sucesso():
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
