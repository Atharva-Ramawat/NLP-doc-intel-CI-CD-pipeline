import os
import json
import redis
import io
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from minio import Minio

app = FastAPI(title="Document Ingestion API")

# Enable CORS (Cross-Origin Resource Sharing) for Frontend Dashboard compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your laptop's browser to connect seamlessly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration Environment Variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
MINIO_HOST = os.getenv("MINIO_HOST", "minio-service:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_PASS = os.getenv("MINIO_ROOT_PASSWORD", "password123")
BUCKET_NAME = "documents"

DB_HOST = os.getenv("DB_HOST", "postgres-service")
DB_NAME = os.getenv("DB_NAME", "doc_intel")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASSWORD", "password123")

# Initialize Cache & Storage Clients
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
minio_client = Minio(MINIO_HOST, access_key=MINIO_USER, secret_key=MINIO_PASS, secure=False)

def get_db_connection():
    """Helper function to create a quick connection to PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

@app.on_event("startup")
def init_storage_and_db():
    # 1. Ensure MinIO bucket exists
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
    except Exception as e:
        print(f"⚠️ MinIO initialization warning: {e}")
        
    # 2. Safely Initialize Database Table Structure across multi-replica setups
    table_creation_query = """
    CREATE TABLE IF NOT EXISTS processed_docs (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255) NOT NULL,
        extracted_text TEXT,
        summary TEXT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(table_creation_query)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database verification complete. Table structure is ready.")
    except Exception as e:
        # Catches the 'relation sequence already exists' error gracefully if another replica runs it simultaneously
        print(f"⚠️ Notice during table initialization (likely handled by concurrent replica): {e}")

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "NLP Document Ingestion API"}

@app.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        file_length = len(file_content)
        
        # 1. Stream the object up to MinIO
        minio_client.put_object(
            BUCKET_NAME,
            file.filename,
            io.BytesIO(file_content),
            length=file_length,
            content_type=file.content_type or "text/plain"
        )
        
        # 2. Push metadata payload to the Redis Job Queue for the NLP worker
        # CORRECTED: Added "object_name" so the worker knows what to search for in MinIO!
        job_payload = {
            "filename": file.filename,
            "bucket": BUCKET_NAME,
            "object_name": file.filename 
        }
        r.rpush("nlp_jobs", json.dumps(job_payload))
        
        return {
            "message": f"Document '{file.filename}' uploaded and queued successfully.",
            "storage_status": "Saved to MinIO",
            "queue_status": "Pushed to queue 'nlp_jobs'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion processing failed: {str(e)}")

@app.get("/documents/")
def get_processed_documents():
    """Fetches all successfully summarized text insights for the Streamlit GUI."""
    try:
        conn = get_db_connection()
        # RealDictCursor parses rows automatically into clean dictionaries/JSON objects
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Added extracted_text into the query selection to properly support your frontend split view
        cur.execute("SELECT id, filename, extracted_text, summary FROM processed_docs ORDER BY id DESC;")
        records = cur.fetchall()
        
        cur.close()
        conn.close()
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query relational database records: {str(e)}")
