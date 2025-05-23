import kombu
from kombu import Connection

# Config - same as in app.py
CELERY_BROKER_URL = "pyamqp://guest@localhost//"
QUEUE_NAMES = ["queue1", "queue2", "queue3"]
RESULT_QUEUE = "result_queue"
MAX_PRIORITY = 10

def reset_queues():
    """Delete and recreate all queues with priority support"""
    with Connection(CELERY_BROKER_URL) as conn:
        channel = conn.channel()
        
        # Process all queues including result queue
        for queue_name in QUEUE_NAMES + [RESULT_QUEUE]:
            try:
                # Delete the queue if it exists
                channel.queue_delete(queue=queue_name)
                print(f"Deleted existing queue: {queue_name}")
            except Exception as e:
                print(f"Queue {queue_name} may not exist: {e}")
            
            try:
                # Recreate the queue with priority support
                channel.queue_declare(
                    queue=queue_name, 
                    durable=True,
                    arguments={"x-max-priority": MAX_PRIORITY}
                )
                print(f"Created queue with priority support: {queue_name}")
            except Exception as e:
                print(f"Error creating queue {queue_name}: {e}")

if __name__ == "__main__":
    print("Resetting queues with priority support...")
    reset_queues()
    print("Done! All queues now have priority support.") 