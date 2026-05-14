import os
import time
import json
import redis

print("🧠 NLP Worker is booting up...")

redis_host = os.getenv("REDIS_HOST", "redis-service")

try:
    r = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
    r.ping()
    print(f"✅ Successfully connected to Redis at {redis_host}")
    print("🎧 Listening for new documents on the 'nlp_jobs' queue...")
    
    while True:
        # blpop waits (blocks) until a job arrives on "nlp_jobs". 
        # The '0' means it will wait forever without timing out.
        queue_name, message = r.blpop("nlp_jobs", 0)
        
        # Convert the JSON string back into a Python dictionary
        job_data = json.loads(message)
        filename = job_data.get("filename")
        
        print(f"\n🚀 NEW JOB RECEIVED: {filename}")
        print(f"⚙️ Running heavy NLP extraction on {filename}...")
        
        # Simulate the time it takes to run an AI model
        time.sleep(5) 
        
        print(f"✅ Finished processing {filename}! Ready for next job.")
        
except Exception as e:
    print(f"❌ Worker crashed or failed to connect: {e}")
    while True:
        time.sleep(10)