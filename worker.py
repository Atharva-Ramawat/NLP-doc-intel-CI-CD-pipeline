import os
import time
import redis

print("🧠 NLP Worker is booting up...")


redis_host = os.getenv("REDIS_HOST", "redis-service")

try:
    r = redis.Redis(host=redis_host, port=6379, db=0)
  
    r.ping()
    print(f"✅ Successfully connected to Redis at {redis_host}")
    print("🎧 Listening for new documents to process...")
    
    while True:
        time.sleep(10)
        
except Exception as e:
    print(f"❌ Failed to connect to Redis: {e}")
    # Still sleep so the container doesn't crash-loop instantly
    while True:
        time.sleep(10)