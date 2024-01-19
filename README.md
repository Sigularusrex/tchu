# chu

I got sick of needing a Pika listener on every app, so I made a small library called Chu, that does it for you. I'll update the docs soon, but essentially you can install Chu:

	chu @ git+https://github.com/Sigularusrex/chu@main


make a management command like this:




	from chu.consumer import ThreadedConsumer
	from django.core.management.base import BaseCommand

	from gc_api.subscribers.chu_callback import chu_callback
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
				callback=chu_callback,
			)
			# Start consuming messages
			consumer.run()
Provide it with a callback function (Mine just blindly publishes to Celery :smile: )
import json

	import celery_pubsub


	def chu_callback(ch, method, properties, body):
		try:
			print("External message received in Service A")
			data = json.loads(body)
			celery_pubsub.publish(method.routing_key, data)
			print("Message published in Service A")
		except Exception as e:
			print(f"Error publishing message: {e}")

...and you're good to go.
