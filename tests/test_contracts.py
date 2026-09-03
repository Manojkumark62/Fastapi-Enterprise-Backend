from fastapi.testclient import TestClient

from main import app


def test_security_headers_and_enterprise_routes_are_published():
    client = TestClient(app)
    response = client.get("/health/live")
    paths = app.openapi()["paths"]

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "/api/v1/auth/forgot-password" in paths
    assert "/api/v1/imports/users" in paths
    assert "/api/v1/payments/{payment_id}/refund" in paths


def test_core_resource_put_endpoints_are_exposed():
    paths = app.openapi()["paths"]

    assert "/api/v1/customers/{customer_id}" in paths
    assert "put" in paths["/api/v1/customers/{customer_id}"]
    assert "/api/v1/employees/{employee_id}" in paths
    assert "put" in paths["/api/v1/employees/{employee_id}"]
    assert "/api/v1/users/{user_id}" in paths
    assert "put" in paths["/api/v1/users/{user_id}"]
    assert "/api/v1/products/{product_id}" in paths
    assert "put" in paths["/api/v1/products/{product_id}"]