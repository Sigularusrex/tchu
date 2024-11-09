import pytest
from tchu.amqp_client import AMQPClient
from unittest.mock import MagicMock, patch

def test_amqp_client_initialization(mock_connection, mock_channel):
    with patch('pika.BlockingConnection', return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel
        client = AMQPClient()
        assert client.connection == mock_connection
        assert client.channel == mock_connection.channel()

def test_setup_exchange(mock_connection, mock_channel):
    with patch('pika.BlockingConnection', return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel
        client = AMQPClient()
        client.setup_exchange("test_exchange", "topic")
        
        mock_channel.exchange_declare.assert_called_once_with(
            exchange="test_exchange",
            exchange_type="topic",
            durable=True
        )

def test_close_connection(mock_connection, mock_channel):
    with patch('pika.BlockingConnection', return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel
        client = AMQPClient()
        client.close()
        mock_connection.close.assert_called_once() 