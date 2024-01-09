import pika
import json
from chu.amqp_client import AMQPClient


class Producer(AMQPClient):
    def publish(self, routing_key, body):
        try:
            properties = pika.BasicProperties(content_type='application/json', delivery_mode=2)

            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=json.dumps(body),
                properties=properties
            )
            print("Message published successfully")
        except Exception as e:
            print(f"Error publishing message: {e}")