# Celery Priority Queue Demo

A demonstration of Celery workers with priority-based message processing using RabbitMQ.

## 📋 Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [How it Works](#how-it-works)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

## ✨ Features

- Multiple queue support with priority-based message processing
- Pre-initialized worker processes with singleton pattern
- Result queue for processed messages
- Support for worker autoscaling

## 📦 Requirements

- Python 3.6+
- RabbitMQ 3.8+
- Celery 5.0+

## 🚀 Installation

1. **Install required dependencies:**
   ```bash
   pip install celery kombu pika
   ```

2. **Make sure RabbitMQ is running:**
   ```bash
   # Start RabbitMQ on Mac
   brew services start rabbitmq
   
   # Or on Ubuntu/Debian
   sudo systemctl start rabbitmq-server
   ```

## 📂 Project Structure

- `celery_demo/app.py` - Main Celery application with task definition
- `celery_demo/reset_queues.py` - Script to reset queues with priority support
- `celery_demo/start_worker.sh` - Shell script to start worker with proper settings
- `celery_queue.py` - Script to publish messages with various priorities

## 🔧 Usage

### 1. Reset Queues (Required First Time)

Before starting, run the queue reset script to ensure all queues have priority support:

```bash
python celery_demo/reset_queues.py
```

### 2. Start Celery Worker

Start the Celery worker with priority settings:

```bash
# Using the provided script
chmod +x celery_demo/start_worker.sh
./celery_demo/start_worker.sh

# Or manually
celery -A celery_demo.app worker --loglevel=info --prefetch-multiplier=1 --concurrency=1
```

### 3. Publish Messages

Run the publisher script to send messages with different priorities:

```bash
python celery_queue.py
```

## 🔍 How it Works

### Priority-Based Processing

Messages are processed based on their priority level (1-10, where 10 is highest):
- High priority (10) messages are processed before lower priority ones
- Priority is set in three places:
  - Message properties
  - Task arguments
  - Task keyword arguments

### Pre-Initialized Workers

Each worker process pre-initializes a singleton instance of `DoDumbStuff` when it starts:
- Initialization happens once per worker process
- All tasks within the same process share the instance
- Each worker process (when using autoscale) gets its own separate instance

### Key Configuration

```python
# Priority support
app.conf.worker_prefetch_multiplier = 1  # Critical for priority
app.conf.task_acks_late = True  # Acknowledge after processing

# Queue settings
app.conf.task_queues = {
    queue: {
        "exchange": queue,
        "routing_key": queue,
        "queue_arguments": {"x-max-priority": 10},  # Enable priority
    }
    for queue in QUEUE_NAMES
}
```

## ⚠️ Troubleshooting

If priorities are not working:

1. Make sure the queues are declared with `x-max-priority` argument
2. Set `worker_prefetch_multiplier=1` in your Celery configuration
3. Verify that `priority` is properly set in message properties

## ❓ FAQ

### 1. What is the required message format for Celery?
Celery mandates that the message should include:
- `task`: The name of the task to execute
- `args`: An array containing the positional arguments
- `id`: A unique identifier to track the status of the message
- Other optional fields like `kwargs`, `retries`, etc.

Example:
```json
{
    "id": "unique-task-id",
    "task": "task.check_multi_queue",
    "args": [{"message": "Hello World"}],
    "kwargs": {"priority": 10},
    "retries": 0,
    "eta": null
}
```

### 2. Can I set up a separate worker for each queue?
Yes, it's possible to set up independent workers for each queue. However, this requires maintaining separate shell scripts to handle each worker and might add complexity to logging and workflow management.

To start workers for specific queues:
```bash
# Worker for queue1 only
celery -A celery_demo.app worker --loglevel=info -Q queue1

# Worker for queue2 only
celery -A celery_demo.app worker --loglevel=info -Q queue2
```

### 3. Is priority support implemented?
Yes, priority support is fully implemented. The code includes:
- Queue declaration with `x-max-priority` argument
- Message publishing with priority setting
- Worker configuration for priority-based consumption
- Example tasks with varying priority levels

### 4. How is the workflow object handled between workers?
A singleton pattern is implemented to handle the workflow object. Each worker process gets its own instance of the singleton, which is initialized once when the worker starts.

Note: While the singleton pattern works for sharing state within a process, it is not designed for sharing state across different worker processes. For cross-process state, consider using Redis, a database, or other external storage.
