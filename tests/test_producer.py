import pytest
import json

from unittest.mock import patch

from tchu.producer import Producer


def test_producer_initialization(
    mock_connection, mock_channel, amqp_url, exchange_name, exchange_type
):
    with patch("pika.BlockingConnection", return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel
        producer = Producer(amqp_url, exchange_name, exchange_type)

        assert producer.exchange == exchange_name
        assert producer.exchange_type == exchange_type
        mock_channel.queue_declare.assert_called_once()


def test_publish_message(mock_connection, mock_channel):
    with patch("pika.BlockingConnection", return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel
        producer = Producer()

        test_message = {"test": "data"}
        producer.publish("test.route", test_message)

        mock_channel.basic_publish.assert_called_once()
        call_args = mock_channel.basic_publish.call_args[1]
        assert call_args["routing_key"] == "test.route"
        assert json.loads(call_args["body"]) == test_message


def test_rpc_call(mock_connection, mock_channel):
    with patch("pika.BlockingConnection", return_value=mock_connection):
        mock_connection.channel.return_value = mock_channel
        producer = Producer()

        # Mock response
        producer.response = json.dumps({"response": "data"}).encode()

        result = producer.call("test.route", {"test": "data"}, timeout=1)
        assert result == {"response": "data"}
