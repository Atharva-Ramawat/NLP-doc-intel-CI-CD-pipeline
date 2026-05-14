from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Ingestion API is running"}

def test_upload_document():
    # We create a fake physical file in memory to send to the new endpoint
    fake_file = {"file": ("sample_invoice.pdf", b"dummy file content", "application/pdf")}
    
    response = client.post("/upload/", files=fake_file)
    
    assert response.status_code == 200
    assert "sample_invoice.pdf" in response.json()["message"]