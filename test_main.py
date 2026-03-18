from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Ingestion API is running"}

def test_upload_document():
    response = client.post("/upload/?filename=sample_invoice.pdf")
    assert response.status_code == 200
    assert "sample_invoice.pdf" in response.json()["message"]