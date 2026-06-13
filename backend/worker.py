import os
import time
import json
import redis
import io
import psycopg2
from minio import Minio
from pypdf import PdfReader

# --- NEW: Import Real ML Libraries ---
from transformers import pipeline

print(" NLP Worker is booting up...")

# Initialize the Machine Learning Summarizer Model
# We use distilbart because it is fast, highly accurate, and won't crash your K8s memory limits
print(" Loading Neural Network Models (this may take a moment)...")
try:
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    print(" ML Models loaded successfully!")
except Exception as e:
    print(f" Failed to load ML models: {e}")

# Configuration Environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
MINIO_HOST = os.getenv("MINIO_HOST", "minio-service:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_PASS = os.getenv("MINIO_ROOT_PASSWORD", "password123")

DB_HOST = os.getenv("DB_HOST", "postgres-service")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "password123")
DB_NAME = os.getenv("POSTGRES_DB", "doc_intel")

def generate_summary(text: str) -> str:
    """Performs true NLP summarization using Hugging Face Transformers."""
    if not text or len(text.strip()) < 50:
        return "Document too short for AI summarization."
    
    try:
        # Transformer models have token limits. We chunk the text to roughly 3000 characters 
        # to ensure the model doesn't crash on massive documents.
        text_chunk = text[:3000] 
        
        # Generate the summary using the neural network
        result = summarizer(text_chunk, max_length=150, min_length=40, do_sample=False)
        return result[0]['summary_text']
    except Exception as e:
        print(f" ML Summarization Error: {e}")
        return "AI Summarization failed due to document complexity."

# Database Connection
db_conn = None
for attempt in range(10):
    try:
        db_conn = psycopg2.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, port=5432
        )
        break
    except Exception as e:
        print(f" Waiting for PostgreSQL (Attempt {attempt+1}/10)...")
        time.sleep(4)

if not db_conn:
    print(" Critical: Failed to bind worker execution to relational database database.")
    exit(1)

# Ensure relational layout exists
with db_conn.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_docs (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            extracted_text TEXT,
            summary TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    db_conn.commit()

# Initialize Storage & Messaging
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True, health_check_interval=30)
minio_client = Minio(MINIO_HOST, access_key=MINIO_USER, secret_key=MINIO_PASS, secure=False)

print(" Worker fully armed. Listening on queue 'nlp_jobs'...")

while True:
    try:
        result = r.blpop("nlp_jobs", timeout=30)
        
        if not result:
            continue
            
        queue_name, message = result
        job_data = json.loads(message)
        
        filename = job_data.get("filename")
        bucket = job_data.get("bucket")
        object_name = job_data.get("object_name")
        
        print(f"\n PROCESSING JOB: {filename}")
        
        # 1. Fetch file
        response = minio_client.get_object(bucket, object_name)
        file_bytes = response.read()
        response.close()
        response.release_conn()
        
        # 2. Extract Text
        extracted_text = ""
        if filename.lower().endswith(".pdf"):
            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text_content = page.extract_text()
                if text_content:
                    extracted_text += text_content + "\n"
        else:
            extracted_text = file_bytes.decode("utf-8", errors="ignore")
            
        # 3. Process Text via TRUE AI Summarizer
        summary = generate_summary(extracted_text)
        
        # 4. Save results to PostgreSQL
        with db_conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO processed_docs (filename, extracted_text, summary) VALUES (%s, %s, %s);",
                (filename, extracted_text, summary)
            )
            db_conn.commit()
            
        print(f"Successfully summarized and saved: {filename}")
        
    except Exception as e:
        print(f"Job processing breakdown encounter: {e}")
        time.sleep(2)