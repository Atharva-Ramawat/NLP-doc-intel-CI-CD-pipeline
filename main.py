import os
import json
import redis
import io
from fastapi import FastAPI, File, UploadFile, HTTPException
from minio import Minio

app = FastAPI(title="Document Ingestion API")

# Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
MINIO_HOST = os.getenv("MINIO_HOST", "minio-service:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_PASS = os.getenv("MINIO_ROOT_PASSWORD", "password123")
BUCKET_NAME = "documents"

# Initialize Clients
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
minio_client = Minio(MINIO_HOST, access_key=MINIO_USER, secret_key=MINIO_PASS, secure=False)

@app.on_event("startup")
def init_storage():
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)

@app.get("/")
def read