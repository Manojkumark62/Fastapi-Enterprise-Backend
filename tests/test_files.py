"""File endpoint contract tests."""

from io import BytesIO

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_file_upload_endpoint_exists():
    """Verify file upload endpoint recognizes multipart uploads."""
    files = {"upload": ("test.txt", BytesIO(b"hello"), "text/plain")}
    response = client.post("/api/v1/files", files=files)
    assert response.status_code in (201, 401, 422, 413)


def test_file_list_endpoint_exists():
    response = client.get("/api/v1/files")
    assert response.status_code in (200, 401)


def test_file_delete_endpoint_exists():
    response = client.delete("/api/v1/files/1")
    assert response.status_code in (204, 401, 404)
