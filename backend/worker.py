import os
import time
import json
import redis
import io
import psycopg2
from minio import Minio
from pypdf import PdfReader

print(" NLP Worker is booting up...")

# Configuration Environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
MINIO_HOST = os.getenv("MINIO_HOST", "minio-service:9000")
MINIO_USER = os.getenv("MINIO_ROOT_USER", "admin")
MINIO_PASS = os.getenv("MINIO_ROOT_PASSWORD", "password123")

DB_HOST = os.getenv("DB_HOST", "postgres-service")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "password123")
DB_NAME = os.getenv("POSTGRES_DB", "doc_intel")

def generate_summary(text: str, max_sentences: int = 3) -> str:
    """Performs an algorithmic summary based on raw text frequency weights."""
    if not text or len(text.strip()) == 0:
        return "Empty document. No content to summarize."
    
    sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 5]
    if len(sentences) <= max_sentences:
        return " ".join(sentences)
        
    # Calculate word frequency weights
    words = text.lower().split()
    freq_dict = {}
    for word in words:
        if len(word) > 4: # basic stop-word mitigation
            freq_dict[word] = freq_dict.get(word, 0) + 1
            
    # Score sentences based on word weights
    sentence_scores = {}
    for index, sentence in enumerate(sentences):
        score = 0
        for word in sentence.lower().split():
            if word in freq_dict:
                score += freq_dict[word]
        sentence_scores[index] = score
        
    # Sort and slice out the top sentences
    top_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_sentences]
    top_indices.sort() # sort sequentially to maintain contextual order
    
    return " ".join([sentences[i] for i in top_indices]) + "."

# Database Connection and Initialization Logic
db_conn = None
for attempt in range(10):
    try:
        db_conn = psycopg2.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, port=5432
        )
        break
    except Exception as e:
        print(f" Waiting for PostgreSQL container to accept connections (Attempt {attempt+1}/10)...")
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
    print(" PostgreSQL database schema verified.")

# Initialize Storage & Messaging hooks
# CORRECTED: Added health_check_interval to prevent Kubernetes from dropping idle network sockets
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True, health_check_interval=30)
minio_client = Minio(MINIO_HOST, access_key=MINIO_USER, secret_key=MINIO_PASS, secure=False)

print(" Worker fully armed. Listening on queue 'nlp_jobs'...")

while True:
    try:
        # CORRECTED: Added a 30-second timeout so the connection gracefully wakes up and retries instead of freezing
        result = r.blpop("nlp_jobs", timeout=30)
        
        # If no message arrived in 30 seconds, result is None. Just loop back and try again!
        if not result:
            continue
            
        queue_name, message = result
        job_data = json.loads(message)
        
        filename = job_data.get("filename")
        bucket = job_data.get("bucket")
        object_name = job_data.get("object_name")
        
        print(f"\n PROCESSING JOB: {filename}")
        
        # 1. Fetch file contents directly from object storage
        response = minio_client.get_object(bucket, object_name)
        file_bytes = response.read()
        response.close()
        response.release_conn()
        
        # 2. Extract Text via File Signature
        extracted_text = ""
        if filename.lower().endswith(".pdf"):
            pdf_file = io.BytesIO(file_bytes)
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text_content = page.extract_text()
                if text_content:
                    extracted_text += text_content + "\n"
        else:
            # Fallback to standard plain text parsing
            extracted_text = file_bytes.decode("utf-8", errors="ignore")
            
        # 3. Process Text via the Summarizer Engine
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
        time.sleep(2) # Prevent rapid loop crashing