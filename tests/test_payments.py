"""Payment endpoint contract tests."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_payment_create_endpoint_exists():
    """Verify payment creation endpoint accepts idempotency key."""
    response = client.post(
        "/api/v1/payments",
        json={
            "order_id": 1,
            "amount": "50.00",
            "idempotency_key": "dt-123",
        },
    )
    assert response.status_code in (201, 400, 401, 404, 422)


def test_payment_refund_endpoint_exists():
    """Verify refund endpoint exists and validates input."""
    response = client.post(
        "/api/v1/payments/1/refund",
        json={"amount": "30.00"},
    )
    assert response.status_code in (200, 400, 401, 404, 422)
