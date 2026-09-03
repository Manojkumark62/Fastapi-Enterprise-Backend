from fastapi.testclient import TestClient

from main import app


def test_business_dashboard_route_is_published():
    client = TestClient(app)
    response = client.get("/api/v1/business/dashboard")
    assert response.status_code in {401, 403, 200}
    assert "/api/v1/business/dashboard" in app.openapi()["paths"]
