from functools import wraps
import logging
import time

# Configure the logger
logging.basicConfig(level=logging.INFO)  # Adjust log level as needed


def run_with_retries(method):
    """
    A decorator that retries a method with a specified number of attempts and delay between retries.

    Args:
    - method (function): The method to be decorated.

    Returns:
    - wrapper (function): The decorated method.

    Note:
    - This decorator is commonly used for functions that involve network operations or connections.
    - It logs retry attempts and delays for troubleshooting purposes.
    - If the maximum number of attempts is reached, a ConnectionError is raised.
    """

    @wraps(method)
    def wrapper(self, **kwargs):
        max_attempts = 10
        current_attempt = 0

        while current_attempt < max_attempts:
            try:
                logging.info(f"Connecting, attempt {current_attempt}")
                response = method(self, **kwargs)
                return
            except Exception as e:
                current_attempt += 1
                if current_attempt < max_attempts:
                    logging.info(
                        f"Error initializing RabbitMQ connection: {e}. Retrying in {current_attempt * 2} seconds..."
                    )
                    time.sleep(current_attempt * 2)
                else:
                    raise ConnectionError(
                        f"Error initializing Pika/RabbitMQ connection: {e}"
                    )

        response = method(**kwargs)

        return response

    return wrapper
