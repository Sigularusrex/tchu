import pika

class AMQPClient:
    def __init__(self, amqp_url='amqp://guest:guest@rabbitmq:5672/', exchange='coolset-events', exchange_type='topic'):
        """
        Initialize the AMQPClient instance.

        Args:
        - amqp_url (str): The URL for the AMQP broker.
        - exchange (str): The exchange name.
        - exchange_type (str): The type of exchange.

        Note:
        - amqp_url: Default is 'amqp://guest:guest@localhost:5672/'.
        - exchange: Default is 'coolset-events'.
        - exchange_type: Default is 'topic'.
        """
        try:
            self.params = pika.URLParameters(amqp_url)
            self.connection = pika.BlockingConnection(self.params)
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange=exchange, exchange_type=exchange_type, durable=True)
        except Exception as e:
            print(f"Error initializing RabbitMQ connection: {e}")

    def close(self):
        self.connection.close()