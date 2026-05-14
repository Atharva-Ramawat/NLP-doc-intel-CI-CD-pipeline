import os
import json
import redis
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

# Connect to the Redis service in Kubernetes
redis_host = os.getenv("REDIS_HOST", "redis-service")
# decode_responses=True automatically converts binary data back to normal strings
r = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "Ingestion API is running"}

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    # 1. Create a "job ticket" with the file details
    job_data = {
        "filename": file.filename,
        "status": "pending_nlp"
    }
    
    # 2. Push the ticket onto the Redis queue named "nlp_jobs"
    try:
        r.lpush("nlp_jobs", json.dumps(job_data))
        queue_status = "Job successfully pushed to Redis queue!"
    except Exception as e:
        queue_status = f"Warning: Failed to reach Redis: {e}"

    return {
        "message": f"Document {file.filename} received.",
        "queue_status": queue_status
    }