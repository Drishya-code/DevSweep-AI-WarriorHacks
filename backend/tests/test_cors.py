from fastapi.testclient import TestClient

from main import app


def test_scan_json_preflight_allows_the_local_vite_fallback_origin():
    origin = "http://localhost:5174"
    response = TestClient(app).options(
        "/api/scan/",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()


def test_cors_preflight_rejects_an_unconfigured_origin():
    response = TestClient(app).options(
        "/api/scan/",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
