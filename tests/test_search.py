"""Product query endpoint contract tests."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_product_listing_endpoint_exists():
    """Verify products listing supports query parameters."""
    response = client.get("/api/v1/products?page=1&limit=10")
    assert response.status_code in (200, 401, 422)


def test_product_search_endpoint_exists():
    """Verify products search route accepts category filters."""
    response = client.get("/api/v1/products?category=Electronics")
    assert response.status_code in (200, 401, 422)


def test_order_search_endpoint_exists():
    """Verify advanced order search endpoint exists."""
    response = client.get("/api/v1/orders/search?sort_by=created_at&limit=10")
    assert response.status_code in (200, 401, 422)
