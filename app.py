from celery import Celery
import kombu
from kombu import Exchange, Queue
import json
import datetime
from celery.signals import worker_init, worker_process_init

CELERY_APP_NAME = "celery_demo"
CELERY_BROKER_URL = "pyamqp://guest@localhost//"

# Define queue names as constants
QUEUE_NAMES = ["queue1", "queue2", "queue3"]
RESULT_QUEUE = "result_queue"  # Queue for publishing results
MAX_PRIORITY = 10  # Maximum priority level


class DoDumbStuff:
    _instance = None  # Class variable to store singleton instance

    def __init__(self, data=None):
        self.data = data
        print(
            f"Initializing DoDumbStuff instance (this should print only once per worker)"
        )

    @classmethod
    def get_instance(cls, data=None):
        """Get or create singleton instance"""
        if cls._instance is None:
            cls._instance = cls(data)
            print("Created new DoDumbStuff instance")
        return cls._instance

    def do_dumb_stuff(self, data=None):
        if data is not None:
            self.data = data
        return self.data


# Pre-initialize the worker - runs once per worker process
@worker_process_init.connect
def initialize_worker(**kwargs):
    # This runs when each worker process starts
    print("Initializing worker process...")
    # Pre-initialize our DoDumbStuff class
    DoDumbStuff.get_instance()
    print("Worker process initialized with DoDumbStuff instance")


app = Celery(
    CELERY_APP_NAME,
    broker=CELERY_BROKER_URL,
)


# Configure queue settings with priority support
app.conf.task_queues = {
    queue: {
        "exchange": queue,
        "routing_key": queue,
        "queue_arguments": {"x-max-priority": MAX_PRIORITY},  # Enable priority
    }
    for queue in QUEUE_NAMES
}

# Add result queue with priority
app.conf.task_create_missing_queues = False  # Ensure queues must be explicitly defined
app.conf.task_default_queue = QUEUE_NAMES[0]  # Default queue
app.conf.worker_prefetch_multiplier = 1  # Important for priority to work properly
app.conf.task_acks_late = True  # Acknowledge tasks after completion

# Configure task routing
app.conf.task_routes = {
    "task.check_multi_queue": {"queue": ",".join(QUEUE_NAMES)},
}


def publish_to_result_queue(result_data, priority=0):
    """
    Publish processed result to the result queue with specified priority

    Args:
        result_data: The data to publish to result queue
        priority: Priority level (0-10, where 10 is highest)
    """
    with kombu.Connection(CELERY_BROKER_URL) as conn:
        # Create exchange and queue for results with priority support
        exchange = Exchange(RESULT_QUEUE, type="direct")
        queue = Queue(
            RESULT_QUEUE,
            exchange=exchange,
            routing_key=RESULT_QUEUE,
            queue_arguments={"x-max-priority": MAX_PRIORITY},  # Enable priority
        )

        with conn.channel() as channel:
            # Declare the queue with priority
            queue.declare(channel=channel)

            # Create producer with json serializer
            producer = kombu.Producer(
                channel, exchange=exchange, routing_key=RESULT_QUEUE, serializer="json"
            )

            # Publish the result with priority
            producer.publish(result_data, priority=priority)  # Set message priority
            print(
                f"Published result to {RESULT_QUEUE} with priority {priority}: {result_data}"
            )


@app.task(name="task.check_multi_queue")
def check_multi_queue(data, priority=0):
    """
    Process data from multiple queues and publish result to result queue

    Args:
        data: The data to process
        priority: Priority level (0-10, where 10 is highest)
    """
    print(f"Received data: {data} with priority: {priority}")

    # Use the pre-initialized singleton instance
    result = DoDumbStuff.get_instance().do_dumb_stuff(data)

    # Publish the result to result queue with the same priority
    publish_to_result_queue(
        {
            "original_data": data,
            "processed_result": result,
            "timestamp": str(datetime.datetime.now()),
            # "priority": priority,
        },
        priority=priority,  # Pass the priority to the result
    )

    return result
