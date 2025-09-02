import pytest
import json
import uuid
from tchu.consumer import Consumer, ThreadedConsumer
from unittest.mock import MagicMock, patch


def test_consumer_initialization(mock_connection, mock_channel):
    with patch("pika.BlockingConnection", return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel

        def callback(ch, method, props, body, rpc):
            pass

        consumer = Consumer(
            exchange="test_exchange", routing_keys=["test.*"], callback=callback
        )

        assert consumer.routing_keys == ["test.*"]
        assert consumer.callback == callback
        mock_channel.queue_bind.assert_called()


def test_callback_wrapper(mock_connection, mock_channel):
    with patch("pika.BlockingConnection", return_value=mock_connection):
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


def test_json_deserialization(mock_connection, mock_channel):
    """Test that JSON messages are automatically deserialized."""
    with patch("pika.BlockingConnection", return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel

        received_body = None

        def test_callback(ch, method, props, body, rpc):
            nonlocal received_body
            received_body = body
            return "response"

        consumer = Consumer(callback=test_callback)

        # Mock message properties with JSON content type
        props = MagicMock()
        props.reply_to = None
        props.content_type = "application/json"
        props.message_id = "test-123"
        method = MagicMock()

        test_data = {"id": str(uuid.uuid4()), "name": "test"}
        json_body = json.dumps(test_data).encode("utf-8")

        consumer.callback_wrapper(mock_channel, method, props, json_body)

        # Verify the callback received the deserialized dict, not raw bytes
        assert received_body == test_data
        mock_channel.basic_ack.assert_called_once()


def test_non_json_content_passthrough(mock_connection, mock_channel):
    """Test that non-JSON content is passed through as bytes."""
    with patch("pika.BlockingConnection", return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel

        received_body = None

        def test_callback(ch, method, props, body, rpc):
            nonlocal received_body
            received_body = body
            return "response"

        consumer = Consumer(callback=test_callback)

        # Mock message properties with non-JSON content type
        props = MagicMock()
        props.reply_to = None
        props.content_type = "text/plain"
        props.message_id = "test-123"
        method = MagicMock()

        test_body = b"plain text message"

        consumer.callback_wrapper(mock_channel, method, props, test_body)

        # Verify the callback received the raw bytes
        assert received_body == test_body
        mock_channel.basic_ack.assert_called_once()


def test_rpc_response_serialization(mock_connection, mock_channel):
    """Test that RPC responses are properly serialized."""
    with patch("pika.BlockingConnection", return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel

        def test_callback(ch, method, props, body, rpc):
            # Return a dict that should be JSON serialized
            return {"result": "success", "id": uuid.uuid4()}

        consumer = Consumer(callback=test_callback)

        # Mock RPC message properties
        props = MagicMock()
        props.reply_to = "callback_queue"
        props.correlation_id = "corr-123"
        props.content_type = "application/json"
        props.message_id = "test-123"
        method = MagicMock()

        test_body = b'{"request": "data"}'

        consumer.callback_wrapper(mock_channel, method, props, test_body)

        # Verify basic_publish was called for RPC response
        mock_channel.basic_publish.assert_called()
        call_args = mock_channel.basic_publish.call_args[1]

        # Verify the response body is JSON serialized
        response_data = json.loads(call_args["body"])
        assert response_data["result"] == "success"
        assert "id" in response_data  # UUID should be serialized as string


def test_threaded_consumer(mock_connection, mock_channel):
    with patch("pika.BlockingConnection", return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel

        consumer = ThreadedConsumer(
            exchange="test_exchange", routing_keys=["test.*"], threads=2
        )

        assert isinstance(consumer, ThreadedConsumer)
        assert consumer.threads == 2
