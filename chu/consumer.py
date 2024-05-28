import threading

from chu.amqp_client import AMQPClient
from chu.utils.retry_decorator import run_with_retries
import logging

# Configure the logger
logging.basicConfig(level=logging.INFO)  # Adjust log level as needed


class ConnectionError(Exception):
    pass


class Consumer(AMQPClient):
    """
    A class for consuming messages from an AMQP broker using RabbitMQ.

    Attributes:
    - exchange (str): The exchange name.
    - exchange_type (str): The type of exchange.
    - amqp_url (str): The URL for the AMQP broker.
    - threads (int): The number of threads for concurrent message processing.
    - routing_keys (list): List of routing keys for binding queues.
    - callback (func): The callback function to be executed when a message is received.
    - queue_name (str): The name of the queue used for message consumption.

    Methods:
    - __init__(amqp_url="amqp://guest:guest@localhost:5672/", exchange="default", exchange_type="topic",
               threads=1, routing_keys=["*"], callback=None):
        Initializes the Consumer instance, sets up the connection, and prepares for message consumption.
    - callback_wrapper(ch, method, properties, body):
        Wraps the callback function to handle received messages and acknowledge them.
    - run():
        Starts the message consumption process.

    Note:
    - The class inherits from AMQPClient, which provides the basic AMQP connection setup.
    - The `run` method is designed to be overridden by subclasses for custom message processing logic.
    """

    @run_with_retries
    def __init__(
        self,
        amqp_url="amqp://guest:guest@localhost:5672/",
        exchange="default",
        exchange_type="topic",
        threads=1,
        routing_keys=["*"],
        callback=None,
    ):
        """
        Initialize the Consumer instance.

        Args:
        - amqp_url (str): The URL for the AMQP broker.
        - exchange (str): The exchange name.
        - exchange_type (str): The type of exchange.
        - threads (int): The number of threads.
        - routing_keys (list): List of routing keys for binding queues.
        - callback (func): The callback function to be executed when a message is received.

        Note:
        - amqp_url: Default is 'amqp://guest:guest@localhost:5672/'.
        - exchange: Default is 'default'.
        - exchange_type: Default is 'topic'.
        - threads: Default is 1.
        - routing_keys: Default is ['*'].
        """

        super().__init__(amqp_url, exchange, exchange_type)
        self.threads = threads
        self.routing_keys = routing_keys if routing_keys else ["coolset.*"]
        self.callback = callback

        try:
            self.channel.basic_qos(prefetch_count=self.threads * 10)
            result = self.channel.queue_declare("", exclusive=True, durable=True)
            self.queue_name = result.method.queue

            for key in self.routing_keys:
                self.channel.queue_bind(
                    exchange=self.exchange, queue=self.queue_name, routing_key=key
                )

            self.channel.basic_consume(
                queue=self.queue_name, on_message_callback=self.callback_wrapper
            )
        except Exception as e:
            ConnectionError(f"Error initializing RabbitMQ connection: {e}")

    def callback_wrapper(self, ch, method, properties, body):
        if self.callback:
            print("Received an event:", body)
            self.callback(ch, method, properties, body)
        else:
            print("Received an event but there is no callback function defined:", body)

        ch.basic_ack(
            delivery_tag=method.delivery_tag, multiple=True
        )  # Acknowledge the message even if no callback is defined

    @run_with_retries
    def run(self):
        self.channel.start_consuming()


class ThreadedConsumer(threading.Thread, Consumer):
    """
    Wraps the callback function to handle received messages and acknowledge them.

    Args:
    - ch (pika.Channel): The communication channel to the AMQP broker.
    - method (pika.spec.Basic.Deliver): Contains delivery information.
    - properties (pika.spec.BasicProperties): Message properties.
    - body (bytes): The message body.

    Note:
    - This method is intended to be overridden by subclasses to provide custom message handling logic.
    """

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        Consumer.__init__(self, *args, **kwargs)

    def run(self):
        Consumer.run(self)
