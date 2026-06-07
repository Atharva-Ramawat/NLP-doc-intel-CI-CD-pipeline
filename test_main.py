import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Create mock clients to bypass connection testing errors
with patch('redis.Redis'), patch('minio.Minio'):
    from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Ingestion API is running"}

@patch('main.minio_client')
@patch('main.r')
def test_upload_document(mock_redis, mock_minio):
    # Configure mock objects to handle method returns smoothly
    mock_minio.put_object.return_value = MagicMock()
    mock_redis.lpush.return_value = 1
    
    fake_file = {"file": ("sample_invoice.pdf", b"dummy file content", "application/pdf")}
    response = client.post("/upload/", files=fake_file)
    
    assert response.status_code == 200
    assert "sample_invoice.pdf" in response.json()["message"]
    assert response.json()["storage_status"] == "Saved to MinIO"