# tchu

`tchu` is a lightweight Python wrapper around Pika/RabbitMQ that simplifies event publishing and consuming in distributed systems. It provides intuitive abstractions for common messaging patterns while handling the underlying RabbitMQ connection management.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/tchu.svg)](https://badge.fury.io/py/tchu)

## Features

- **Simple API** for publishing events and consuming them
- **ThreadedConsumer** for concurrent message processing
- **RPC-style messaging** with request-response pattern support
- **Automatic retries** with configurable backoff
- **Message deduplication** support with optional cache integration
- **Idle handlers** for periodic maintenance tasks
- **Comprehensive logging** of all messaging operations

## Installation

```bash
pip install tchu
```

## Usage

### Producer: Publishing Events

```python
from tchu import Producer

# Initialize a producer
producer = Producer(
    amqp_url="amqp://guest:guest@localhost:5672/",
    exchange="my-exchange",
    exchange_type="topic"
)

# Publish a message
producer.publish(
    routing_key="user.created",
    body={"user_id": "123", "name": "John Doe", "email": "john@example.com"}
)

# Publish a message and wait for a response (RPC-style)
try:
    response = producer.call(
        routing_key="user.validate",
        body={"user_id": "123", "email": "john@example.com"},
        timeout=5  # seconds
    )
    print(f"Response received: {response}")
except TimeoutError:
    print("No response received within timeout period")
```

### Consumer: Processing Events

#### Basic Consumer

```python
from tchu import Consumer

def message_handler(ch, method, properties, body, is_rpc):
    print(f"Received message: {body}")
    if is_rpc:
        # For RPC calls, return a response
        return json.dumps({"status": "success", "message": "Validation completed"})

# Initialize a consumer
consumer = Consumer(
    amqp_url="amqp://guest:guest@localhost:5672/",
    exchange="my-exchange",
    exchange_type="topic",
    routing_keys=["user.*"],  # Listen to all user events
    callback=message_handler,
    prefetch_count=10  # Process up to 10 messages at once
)

# Start consuming messages
consumer.run()
```

#### Threaded Consumer with Django Management Command

```python
# management/commands/listen_for_events.py
from tchu import ThreadedConsumer
from django.core.management.base import BaseCommand
from django.conf import settings
import json

def event_callback(ch, method, properties, body, is_rpc):
    try:
        print(f"Received event: {method.routing_key}")
        data = json.loads(body)
        
        # Process the event data
        # ...
        
        print("Event processed successfully")
    except Exception as e:
        print(f"Error processing event: {e}")


class Command(BaseCommand):
    help = "Starts a listener for RabbitMQ events"

    def handle(self, *args, **options):
        consumer = ThreadedConsumer(
            amqp_url=settings.RABBITMQ_BROKER_URL,
            exchange="app-events",
            exchange_type="topic",
            threads=5,  # Use 5 worker threads
            routing_keys=["user.*", "order.created"],
            callback=event_callback,
        )
        
        # Start consuming messages in a separate thread
        consumer.start()
        
        # Keep the main thread running
        self.stdout.write("Event listener started. Press Ctrl+C to stop.")
        try:
            consumer.join()
        except KeyboardInterrupt:
            self.stdout.write("Stopping event listener...")
```

### Advanced Features

#### Using with Cache for Message Deduplication

```python
from django.core.cache import cache
from tchu import ThreadedConsumer

# Cache adapter that implements the required interface
class DjangoCache:
    def add(self, key, value, timeout=300):
        return cache.add(key, value, timeout)

# Initialize consumer with cache
consumer = ThreadedConsumer(
    amqp_url="amqp://guest:guest@localhost:5672/",
    exchange="my-exchange",
    exchange_type="topic",
    routing_keys=["user.*"],
    callback=message_handler,
    cache=DjangoCache(),
    cache_key_prefix="myapp"  # Prefix for cache keys
)
```

#### Idle Handler for Periodic Tasks

```python
def maintenance_task():
    print("Performing periodic maintenance...")
    # Clean up resources, update statistics, etc.

consumer = Consumer(
    # ... other parameters
    idle_handler=maintenance_task,
    idle_interval=3600  # Run maintenance every hour
)
```

## API Reference

### AMQPClient

Base class for both Producer and Consumer.

- `__init__(amqp_url="amqp://guest:guest@localhost:5672/")`
- `setup_exchange(exchange, exchange_type)`
- `close()`

### Producer

- `__init__(amqp_url, exchange, exchange_type)`
- `publish(routing_key, body, content_type, delivery_mode)`
- `call(routing_key, body, content_type, delivery_mode, timeout)`

### Consumer

- `__init__(amqp_url, exchange, exchange_type, threads, routing_keys, callback, idle_handler, idle_interval, prefetch_count, cache, cache_key_prefix)`
- `run()`

### ThreadedConsumer

Extends Consumer to run in a separate thread.

## Development

1. Clone the repository
2. Install dependencies: `poetry install`
3. Run tests: `poetry run pytest`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
