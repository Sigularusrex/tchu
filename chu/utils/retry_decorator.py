from functools import wraps
import logging
import time

# Configure the logger
logging.basicConfig(level=logging.INFO)  # Adjust log level as needed


def run_with_retries(method):
    @wraps(method)
    def wrapper(self, **kwargs):
        max_attempts = 10
        current_attempt = 0

        while current_attempt < max_attempts:
            try:
                logging.info(f"Connecting, attempt {current_attempt}")
                response = method(**kwargs)
                return
            except Exception as e:
                current_attempt += 1
                if current_attempt < max_attempts:
                    logging.info(
                        f"Error initializing RabbitMQ connection: {e}. Retrying in {current_attempt * 2} seconds..."
                    )
                    time.sleep(current_attempt * 2)
                else:
                    ConnectionError(f"Error initializing Pika/RabbitMQ connection: {e}")

        response = method(**kwargs)

        return response

    return wrapper
