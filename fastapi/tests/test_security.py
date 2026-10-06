import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef")

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from database import get_session
from main import app
from models.tables import Prediction, User
from security.auth import create_access_token


@pytest.fixture()
def ctx(tmp_path):
    """Banco SQLite temporário + 2 usuários (admin/alice), cada um com 1 predição."""
    engine = create_engine(
        f"sqlite:///{tmp_path/'test.db'}", connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)
    pw = bcrypt.hashpw(b"senha", bcrypt.gensalt()).decode()
    with Session(engine) as s:
        admin, alice = User(username="admin", hashed_password=pw), User(username="alice", hashed_password=pw)
        s.add(admin); s.add(alice); s.commit()
        p_admin = Prediction(owner_id=admin.id, text="texto do admin", intent="Refund Request", confidence=0.9)
        p_alice = Prediction(owner_id=alice.id, text="texto da alice", intent="Billing Inquiry", confidence=0.85)
        s.add(p_admin); s.add(p_alice); s.commit()
        ids = {"admin": p_admin.id, "alice": p_alice.id}

    def _session():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = _session
    yield TestClient(app), engine, ids
    app.dependency_overrides.clear()


def _auth(username: str) -> dict:
    # token gerado direto (evita bater no rate limit de 10/min do /auth/token)
    return {"Authorization": f"Bearer {create_access_token({'sub': username})}"}


def test_acesso_sem_token_retorna_401(ctx):
    client, _, ids = ctx
    for method, url, kw in [
        ("GET", "/predict", {}),
        ("GET", f"/predict/{ids['admin']}", {}),
        ("POST", "/predict", {"json": {"text": "quero reembolso"}}),
    ]:
        r = client.request(method, url, **kw)
        assert r.status_code == 401, f"{method} {url} deveria exigir token"
        assert r.headers["www-authenticate"] == "Bearer"


def test_acesso_a_recurso_de_outro_usuario_retorna_404(ctx):
    client, _, ids = ctx
    # alice tenta ler a predição do admin -> 404 (não revela que existe)
    r = client.get(f"/predict/{ids['admin']}", headers=_auth("alice"))
    assert r.status_code == 404
    assert "texto do admin" not in r.text
    # a listagem da alice só traz as dela
    r = client.get("/predict", headers=_auth("alice"))
    assert r.status_code == 200
    assert [p["id"] for p in r.json()] == [ids["alice"]]
    # a própria predição continua acessível
    assert client.get(f"/predict/{ids['alice']}", headers=_auth("alice")).status_code == 200


def test_campo_extra_no_body_e_rejeitado(ctx):
    client, engine, _ = ctx
    with Session(engine) as s:
        antes = len(s.exec(select(Prediction)).all())
    r = client.post(
        "/predict",
        headers=_auth("alice"),
        json={"text": "quero reembolso", "owner_id": 1, "is_admin": True},
    )
    assert r.status_code == 422
    assert {e["type"] for e in r.json()["detail"]} == {"extra_forbidden"}
    with Session(engine) as s:  # nada foi gravado
        assert len(s.exec(select(Prediction)).all()) == antes
