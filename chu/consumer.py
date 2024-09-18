import threading
import logging
import time
import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties
from typing import Callable, Optional, List
from chu.amqp_client import AMQPClient
from chu.utils.retry_decorator import run_with_retries


# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    """

    @run_with_retries
    def __init__(
        self,
        amqp_url: str = "amqp://guest:guest@localhost:5672/",
        exchange: str = "default",
        exchange_type: str = "topic",
        threads: int = 1,
        routing_keys: Optional[List[str]] = ["*"],
        callback: Optional[
            Callable[
                [BlockingChannel, Basic.Deliver, BasicProperties, bytes, bool], None
            ]
        ] = None,
        idle_handler: Optional[Callable[[], None]] = None,
        idle_interval: int = 3600,
    ) -> None:
        """
        Initialize the Consumer instance.

        This method sets up the AMQP connection, configures the exchange and queue,
        and prepares for message consumption. It also initializes the idle handler
        functionality for performing periodic tasks.

        Args:
        - amqp_url (str): The URL for the AMQP broker. Defaults to "amqp://guest:guest@localhost:5672/".
        - exchange (str): The name of the exchange to use. Defaults to "default".
        - exchange_type (str): The type of exchange (e.g., "topic", "direct", "fanout"). Defaults to "topic".
        - threads (int): The number of threads for concurrent message processing. Defaults to 1.
        - routing_keys (list): List of routing keys for binding queues. Defaults to ["*"].
        - callback (Callable): The callback function to be executed when a message is received.
            It should accept the following parameters:
            - ch (BlockingChannel): The channel object.
            - method (Basic.Deliver): The message delivery information.
            - properties (BasicProperties): The message properties.
            - body (bytes): The message body.
            - RPC (bool): Indicates whether this is an RPC call.
        - idle_handler (Callable): A function to be called periodically during idle time.
            It takes no parameters and is used for maintenance tasks. Defaults to None.
        - idle_interval (int): The interval in seconds between idle handler calls. Defaults to 3600 (1 hour).

        Raises:
        - ConnectionError: If there's an error initializing the RabbitMQ connection.
        """
        super().__init__(amqp_url)
        self.threads = threads
        self.routing_keys = routing_keys
        self.callback = callback
        self.idle_handler = idle_handler
        self.idle_interval = idle_interval
        self.last_idle_time = time.time()
        self._stop_event = threading.Event()

        try:
            self.setup_exchange(exchange, exchange_type)
            self.channel.basic_qos(prefetch_count=self.threads)
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
            logger.error(f"Error initializing RabbitMQ connection: {e}")
            raise ConnectionError(f"Error initializing RabbitMQ connection: {e}")

    def callback_wrapper(
        self,
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        logger.info(f"Received an event: {body}")
        RPC = properties.reply_to is not None
        if self.callback:
            try:
                response = self.callback(ch, method, properties, body, RPC)
                if RPC:
                    reply_properties = pika.BasicProperties(
                        correlation_id=properties.correlation_id
                    )
                    self.channel.basic_publish(
                        exchange="",
                        routing_key=properties.reply_to,
                        body=response,
                        properties=reply_properties,
                    )
                ch.basic_ack(delivery_tag=method.delivery_tag, multiple=True)
            except Exception as e:
                logger.error(f"Error in callback processing: {e}")
                # Even if there is an error, we still acknowledge the message to avoid reprocessing
                ch.basic_ack(delivery_tag=method.delivery_tag, multiple=True)
                # leaving the 'nack' here for the future in case we want to retry the message (nack is negative acknowledgment)
                # ch.basic_nack(delivery_tag=method.delivery_tag, multiple=True)
        else:
            logger.warning(
                "Received an event but there is no callback function defined"
            )
            ch.basic_ack(delivery_tag=method.delivery_tag, multiple=True)

    @run_with_retries
    def run(self):
        logger.info("Starting message consumption")
        while not self._stop_event.is_set():
            # Process messages for a short time
            self.connection.process_data_events(time_limit=60)  # Process for 1 minute

            # Check if it's time to call the idle handler
            current_time = time.time()
            if self.idle_handler and (
                current_time - self.last_idle_time >= self.idle_interval
            ):
                try:
                    self.idle_handler()
                except Exception as e:
                    logger.error(f"Error in idle handler: {e}")
                finally:
                    self.last_idle_time = current_time


class ThreadedConsumer(threading.Thread, Consumer):
    """
    A class that wraps the Consumer class to handle message consumption in a separate thread.
    """

    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        threading.Thread.__init__(self)
        Consumer.__init__(self, *args, **kwargs)

    def run(self):
        Consumer.run(self)
