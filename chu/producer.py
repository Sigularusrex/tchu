from typing import Union
import logging
import pika
import json
import uuid
import time
from chu.amqp_client import AMQPClient

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Producer(AMQPClient):
    """
    A class for publishing messages to an AMQP broker using RabbitMQ.

    Methods:
    - publish(routing_key, body, content_type='application/json', delivery_mode=2):
        Publishes a message to the specified routing key on the AMQP broker.
    - call(routing_key, body, content_type='application/json', delivery_mode=2, timeout=30):
        Sends a message to the specified routing key and waits for a response.
    """

    def __init__(
        self,
        amqp_url: str = "amqp://guest:guest@localhost:5672/",
        exchange: str = "default",
        exchange_type: str = "topic",
    ):
        """
        Initialize the Producer instance and setup the exchange.

        Args:
        - amqp_url (str): The URL for the AMQP broker. Default is 'amqp://guest:guest@localhost:5672/'.
        - exchange (str): The exchange name. Default is 'default'.
        - exchange_type (str): The exchange type. Default is 'topic'.
        """
        super().__init__(amqp_url)
        self.setup_exchange(exchange, exchange_type)

        # Declare a callback queue for receiving responses
        result = self.channel.queue_declare(queue="", exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True,
        )

        self.response = None
        self.corr_id = None

    def publish(
        self,
        routing_key: str,
        body: Union[dict, str],
        content_type: str = "application/json",
        delivery_mode: int = 2,
    ):
        """
        Publish a message to the specified routing key on the AMQP broker.

        Args:
        - routing_key (str): The routing key for message routing.
        - body (dict): The message body, typically a dictionary to be JSON-serialized.
        - content_type (str): The MIME type of the message content. Default is 'application/json'.
        - delivery_mode (int): The delivery mode for the message (1 for non-persistent, 2 for persistent).
                              Default is 2 (persistent).

        Raises:
        - Exception: If there is an error during the message publishing process.
        """
        try:
            properties = pika.BasicProperties(
                content_type=content_type, delivery_mode=delivery_mode
            )
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(body),
                properties=properties,
            )
            logger.info("Message published successfully")
        except Exception as e:
            logger.error(f"Error publishing message: {e}")

    def on_response(
        self,
        ch: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        props: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(
        self,
        routing_key: str,
        body: Union[dict, str],
        content_type: str = "application/json",
        delivery_mode: int = 2,
        timeout: int = 30,
    ):
        """
        Send a message to the specified routing key and wait for a response.

        Args:
        - routing_key (str): The routing key for message routing.
        - body (dict): The message body, typically a dictionary to be JSON-serialized.
        - content_type (str): The MIME type of the message content. Default is 'application/json'.
        - delivery_mode (int): The delivery mode for the message (1 for non-persistent, 2 for persistent).
                              Default is 2 (persistent).
        - timeout (int): The timeout for waiting for a response, in seconds. Default is 30 seconds.

        Returns:
        - The response message body.

        Raises:
        - TimeoutError: If no response is received within the specified timeout period.
        """
        self.response = None
        self.corr_id = str(uuid.uuid4())

        properties = pika.BasicProperties(
            reply_to=self.callback_queue,
            correlation_id=self.corr_id,
            content_type=content_type,
            delivery_mode=delivery_mode,
            priority=5,
        )
        try:
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(body),
                properties=properties,
            )
            logger.info("RPC called successfully")
        except Exception as e:
            logger.error(f"Error calling RPC - message: {e}")

        start_time = time.time()
        while self.response is None and (time.time() - start_time) < timeout:
            self.connection.process_data_events(time_limit=timeout)

        if self.response is None:
            raise TimeoutError("No response received within the timeout period")

        return json.loads(self.response)
