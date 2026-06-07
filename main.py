import os
import json
import redis
from fastapi import FastAPI, File, UploadFile, HTTPException
from minio import Minio
import io

app = FastAPI(title="Document Ingestion API")

# Infrastructure Handshakes
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
MINIO_HOST = os.getenv("MINIO_HOST", "minio-service:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_PASS = os.getenv("MINIO_ROOT_PASSWORD", "password123")

# Initialize Clients
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
minio_client = Minio(
    MINIO_HOST,
    access_key=MINIO_USER,
    secret_key=MINIO_PASS,
    secure=False
)

BUCKET_NAME = "documents"

@app.on_event("startup")
def init_storage():
    """Ensure the target object storage bucket exists on startup."""
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
            print(f" Created storage bucket: {BUCKET_NAME}")
    except Exception as e:
        print(f" MinIO initialization warning: {e}")

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "Ingestion API is running"}

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename
    file_content = await file.read()
    file_length = len(file_content)
    
    if file_length == 0:
        raise HTTPException(status_code=400, detail="Cannot upload an empty file.")

    # 1. Stream the object safely into MinIO storage
    try:
        minio_client.put_object(
            bucket_name=BUCKET_NAME,
            object_name=filename,
            data=io.BytesIO(file_content),
            length=file_length,
            content_type=file.content_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Object Storage failure: {e}")

    # 2. Construct the tracking ticket for async workers
    job_data = {
        "filename": filename,
        "bucket": BUCKET_NAME,
        "object_name": filename
    }
    
    # 3. Publish onto the Redis cluster line
    try:
        r.lpush("nlp_jobs", json.dumps(job_data))
        queue_status = "Job successfully queued for NLP engine tracking."
    except Exception as e:
        queue_status = f"Warning: Message failed to broadcast to Redis: {e}"

    return {
        "message": f"Document {filename} processed successfully.",
        "storage_status": "Saved to MinIO",
        "queue_status": queue_status
    }