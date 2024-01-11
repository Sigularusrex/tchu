import pika
import json
from chu.amqp_client import AMQPClient


class Producer(AMQPClient):
    """
    A class for publishing messages to an AMQP broker using RabbitMQ.

    Attributes:
    - exchange (str): The exchange name.
    - exchange_type (str): The type of exchange.
    - amqp_url (str): The URL for the AMQP broker.

    Methods:
    - publish(routing_key, body, content_type='application/json', delivery_mode=2):
        Publishes a message to the specified routing key on the AMQP broker.

    Note:
    - The class inherits from AMQPClient, which provides the basic AMQP connection setup.
    """

    def publish(
        self, routing_key, body, content_type="application/json", delivery_mode=2
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
            # Define message properties (content type and delivery mode)
            properties = pika.BasicProperties(
                content_type=content_type, delivery_mode=delivery_mode
            )

            # Publish the message to the specified exchange and routing key
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(body),
                properties=properties,
            )
            print("Message published successfully")
        except Exception as e:
            print(f"Error publishing message: {e}")
