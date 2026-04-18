from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "cloud-api"
    assert data["status"] == "ok"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_ready():
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "uptime_seconds" in data


def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "cloud_api_requests_total" in response.text


def test_security_headers():
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
