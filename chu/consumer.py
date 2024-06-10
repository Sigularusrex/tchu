import threading
import logging
import pika
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
        """
        super().__init__(amqp_url)
        self.threads = threads
        self.routing_keys = routing_keys
        self.callback = callback

        try:
            self.setup_exchange(exchange, exchange_type)
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
            logger.error(f"Error initializing RabbitMQ connection: {e}")
            raise ConnectionError(f"Error initializing RabbitMQ connection: {e}")

    def callback_wrapper(self, ch, method, properties, body):
        logger.info(f"Received an event: {body}")
        RPC = "reply_to" in properties
        if self.callback:
            try:
                response = self.callback(ch, method, properties, body)
                if RPC:
                    reply_properties = pika.BasicProperties(
                        correlation_id=properties.correlation_id
                    )
                    self.channel.basic_publish(
                        exchange="",
                        routing_key=properties.reply_to,
                        properties=reply_properties,
                        body=response,
                    )
                ch.basic_ack(delivery_tag=method.delivery_tag, multiple=True)
            except Exception as e:
                logger.error(f"Error in callback processing: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, multiple=True)
        else:
            logger.warning(
                "Received an event but there is no callback function defined"
            )
            ch.basic_ack(delivery_tag=method.delivery_tag, multiple=True)

    @run_with_retries
    def run(self):
        logger.info("Starting message consumption")
        self.channel.start_consuming()


class ThreadedConsumer(threading.Thread, Consumer):
    """
    A class that wraps the Consumer class to handle message consumption in a separate thread.
    """

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        Consumer.__init__(self, *args, **kwargs)

    def run(self):
        Consumer.run(self)
