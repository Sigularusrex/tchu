import pika


class AMQPClient:
    """
    A base class for interacting with an AMQP broker using RabbitMQ.

    Attributes:
    - amqp_url (str): The URL for the AMQP broker.
    - exchange (str): The exchange name.
    - exchange_type (str): The type of exchange.
    - params (pika.URLParameters): Parameters for connecting to the AMQP broker.
    - connection (pika.BlockingConnection): The connection to the AMQP broker.
    - channel (pika.Channel): The communication channel to the AMQP broker.

    Methods:
    - __init__(amqp_url="amqp://guest:guest@localhost:5672/", exchange="default", exchange_type="topic"):
        Initializes the AMQPClient instance and establishes a connection to the AMQP broker.
    - close():
        Closes the connection to the AMQP broker.

    Note:
    - The class sets up a connection to RabbitMQ upon initialization and declares an exchange with specified properties.
    - The `close` method is provided to close the connection when it is no longer needed.
    """

    def __init__(
        self,
        amqp_url="amqp://guest:guest@localhost:5672/",
        exchange="default",
        exchange_type="topic",
    ):
        """
        Initialize the AMQPClient instance.

        Args:
        - amqp_url (str): The URL for the AMQP broker.
        - exchange (str): The exchange name.
        - exchange_type (str): The type of exchange.

        Note:
        - amqp_url: Default is 'amqp://guest:guest@localhost:5672/'.
        - exchange: Default is 'default'.
        - exchange_type: Default is 'topic'.
        """
        try:
            self.params = pika.URLParameters(amqp_url)
            self.connection = pika.BlockingConnection(self.params)
            self.channel = self.connection.channel()
            self.exchange = exchange
            self.channel.exchange_declare(
                exchange=exchange, exchange_type=exchange_type, durable=True
            )
        except Exception as e:
            print(f"Error initializing RabbitMQ connection: {e}")
            raise

    def close(self):
        self.connection.close()
