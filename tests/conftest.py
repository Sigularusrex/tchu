import pytest
import pika
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_connection():
    with patch('pika.BlockingConnection') as mock:
        yield mock

@pytest.fixture
def mock_channel():
    channel = MagicMock()
    channel.basic_publish = MagicMock()
    channel.queue_declare = MagicMock()
    channel.basic_consume = MagicMock()
    return channel

@pytest.fixture
def amqp_url():
    return "amqp://guest:guest@localhost:5672/"

@pytest.fixture
def exchange_name():
    return "test_exchange"

@pytest.fixture
def exchange_type():
    return "topic" 