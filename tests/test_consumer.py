import pytest
from tchu.consumer import Consumer, ThreadedConsumer
from unittest.mock import MagicMock, patch

def test_consumer_initialization(mock_connection, mock_channel):
    with patch('pika.BlockingConnection', return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel
        
        def callback(ch, method, props, body, rpc):
            pass
        
        consumer = Consumer(
            exchange="test_exchange",
            routing_keys=["test.*"],
            callback=callback
        )
        
        assert consumer.routing_keys == ["test.*"]
        assert consumer.callback == callback
        mock_channel.queue_bind.assert_called()

def test_callback_wrapper(mock_connection, mock_channel):
    with patch('pika.BlockingConnection', return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel
        
        callback_called = False
        def test_callback(ch, method, props, body, rpc):
            nonlocal callback_called
            callback_called = True
            return "response"
        
        consumer = Consumer(callback=test_callback)
        
        # Mock message properties
        props = MagicMock()
        props.reply_to = None
        method = MagicMock()
        
        consumer.callback_wrapper(mock_channel, method, props, b'{"test": "data"}')
        assert callback_called
        mock_channel.basic_ack.assert_called_once()

def test_threaded_consumer(mock_connection, mock_channel):
    with patch('pika.BlockingConnection', return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel
        
        consumer = ThreadedConsumer(
            exchange="test_exchange",
            routing_keys=["test.*"],
            threads=2
        )
        
        assert isinstance(consumer, ThreadedConsumer)
        assert consumer.threads == 2 