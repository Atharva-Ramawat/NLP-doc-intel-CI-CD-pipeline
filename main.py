

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "Ingestion API is running"}

@app.post("/upload/")
def upload_document(filename: str):
    return {"message": f"Document {filename} received for NLP processing."}