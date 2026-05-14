from fastapi import FastAPI, File, UploadFile

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "Ingestion API is running"}

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    # file.filename automatically extracts the name of the file you uploaded
    return {"message": f"Document {file.filename} received for NLP processing."}