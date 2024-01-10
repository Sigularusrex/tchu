import pika
import json
import threading
import time
from chu.amqp_client import AMQPClient


class Consumer(AMQPClient):
    def __init__(self, amqp_url='amqp://guest:guest@rabbitmq:5672/', exchange='coolset-events', exchange_type='topic', threads=1, routing_keys=['*'], callback=None):
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
        self.routing_keys = routing_keys if routing_keys else ['coolset.*']
        self.callback = callback

        try:
            self.channel.basic_qos(prefetch_count=self.threads*10)
            result = self.channel.queue_declare('', exclusive=True, durable=True)
            self.queue_name = result.method.queue

            for key in self.routing_keys:
                self.channel.queue_bind(exchange=self.exchange, queue=self.queue_name, routing_key=key)

            self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback_wrapper)
        except Exception as e:
            raise f"Error initializing RabbitMQ connection: {e}"

    def callback_wrapper(self, ch, method, properties, body):
        if self.callback:
            self.callback(ch, method, properties, body)
        else:
            print("Received an event but there is no callback function defined:", body)

        ch.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge the message even if no callback is defined


    def run(self):
        max_attempts = 10
        current_attempt = 0

        while current_attempt < max_attempts:
            try:
                self.channel.start_consuming()
                return
            except Exception as e:
                current_attempt += 1
                if current_attempt < max_attempts:
                    print(f"Error initializing RabbitMQ connection: {e}. Retrying in {current_attempt * 2} seconds...")
                    time.sleep(current_attempt * 2)
                else:
                    raise f"Error initializing Pika/RabbitMQ connection: {e}"
        print("Started Consumer Thread")


class ThreadedConsumer(threading.Thread, Consumer):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        Consumer.__init__(self, *args, **kwargs)

    def run(self):
        Consumer.run(self)