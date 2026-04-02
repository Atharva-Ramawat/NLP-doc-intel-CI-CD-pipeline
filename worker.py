import os
import time
import redis

print("🧠 NLP Worker is booting up...")

# Grab the Redis host from the environment variables we set in Kubernetes
redis_host = os.getenv("REDIS_HOST", "redis-service")

try:
    # Connect to the Message Queue
    r = redis.Redis(host=redis_host, port=6379, db=0)
    # Ping it to make sure it's alive
    r.ping()
    print(f"✅ Successfully connected to Redis at {redis_host}")
    print("🎧 Listening for new documents to process...")
    
    # Infinite loop to keep the container alive and waiting for tasks
    while True:
        time.sleep(10)
        
except Exception as e:
    print(f"❌ Failed to connect to Redis: {e}")
    # Still sleep so the container doesn't crash-loop instantly
    while True:
        time.sleep(10)