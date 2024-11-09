# tchu

A lightweight Python wrapper around Pika/RabbitMQ for easy event publishing and consuming.

## Installation

	chu @ git+https://github.com/Sigularusrex/tchu@main


make a management command like this:




	from tchu.consumer import ThreadedConsumer
	from django.core.management.base import BaseCommand

	from gc_api.subscribers.tchu_callback import tchu_callback
	from settings import RABBITMQ_BROKER_URL


	class Command(BaseCommand):
		help = "Launches Listener for Service A events: RabbitMQ"

		def handle(self, *args, **options):
			consumer = ThreadedConsumer(
				amqp_url=RABBITMQ_BROKER_URL,
				exchange="exchange-name",
				exchange_type="topic",
				threads=5,
				routing_keys=["event_topic.*"],
				callback=tchu_callback,
			)
			# Start consuming messages
			consumer.run()
Provide it with a callback function (Mine just blindly publishes to Celery :smile: )
import json

	import celery_pubsub


	def tchu_callback(ch, method, properties, body):
		try:
			print("External message received in Service A")
			data = json.loads(body)
			celery_pubsub.publish(method.routing_key, data)
			print("Message published in Service A")
		except Exception as e:
			print(f"Error publishing message: {e}")

...and you're good to go.
