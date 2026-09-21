from fastapi.testclient import TestClient
from app.main import app
from app.config import load_config

client = TestClient(app)


def test_auth_unauthorized():
    # 无任何 key
    response = client.get("/api/config")
    assert response.status_code == 401

    # 错误 key
    response2 = client.get("/api/config", headers={"X-Admin-Key": "wrong-password"})
    assert response2.status_code == 401


def test_auth_authorized():
    config = load_config()
    valid_key = config.security.admin_password

    response = client.get("/api/config", headers={"X-Admin-Key": valid_key})
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "recipient" in data["data"]


def test_status_endpoint():
    config = load_config()
    valid_key = config.security.admin_password

    response = client.get("/api/status", headers={"X-Admin-Key": valid_key})
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
    assert "daily_time" in data["data"]


def test_preview_endpoint():
    config = load_config()
    valid_key = config.security.admin_password

    response = client.get(f"/api/preview?key={valid_key}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "早安" in response.text


def test_update_config():
    config = load_config()
    valid_key = config.security.admin_password

    payload = config.model_dump()
    payload["basic"]["city"] = "成都"

    response = client.post("/api/config", json=payload, headers={"X-Admin-Key": valid_key})
    assert response.status_code == 200
    assert response.json()["code"] == 0

    # 验证读取
    check_res = client.get("/api/config", headers={"X-Admin-Key": valid_key})
    assert check_res.json()["data"]["basic"]["city"] == "成都"
