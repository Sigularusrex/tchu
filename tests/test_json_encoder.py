"""
Tests for the JSON encoder utility module.
"""

import pytest
import json
import uuid
import datetime
import decimal
from tchu.utils.json_encoder import dumps_message, loads_message


class TestMessageJSONEncoder:
    """Test cases for the MessageJSONEncoder class."""

    def test_uuid_serialization(self):
        """Test that UUID objects are properly serialized to strings."""
        test_uuid = uuid.uuid4()
        test_data = {"id": test_uuid, "name": "test"}

        result = dumps_message(test_data)
        parsed = json.loads(result)

        assert parsed["id"] == str(test_uuid)
        assert parsed["name"] == "test"

    def test_datetime_serialization(self):
        """Test that datetime objects are properly serialized to ISO format."""
        test_datetime = datetime.datetime(2024, 1, 15, 10, 30, 45)
        test_data = {"timestamp": test_datetime, "event": "test"}

        result = dumps_message(test_data)
        parsed = json.loads(result)

        assert parsed["timestamp"] == "2024-01-15T10:30:45"
        assert parsed["event"] == "test"

    def test_date_serialization(self):
        """Test that date objects are properly serialized to ISO format."""
        test_date = datetime.date(2024, 1, 15)
        test_data = {"date": test_date, "event": "test"}

        result = dumps_message(test_data)
        parsed = json.loads(result)

        assert parsed["date"] == "2024-01-15"
        assert parsed["event"] == "test"

    def test_time_serialization(self):
        """Test that time objects are properly serialized to ISO format."""
        test_time = datetime.time(10, 30, 45)
        test_data = {"time": test_time, "event": "test"}

        result = dumps_message(test_data)
        parsed = json.loads(result)

        assert parsed["time"] == "10:30:45"
        assert parsed["event"] == "test"

    def test_decimal_serialization(self):
        """Test that Decimal objects are properly serialized to float."""
        test_decimal = decimal.Decimal("123.45")
        test_data = {"amount": test_decimal, "currency": "USD"}

        result = dumps_message(test_data)
        parsed = json.loads(result)

        assert parsed["amount"] == 123.45
        assert parsed["currency"] == "USD"

    def test_set_serialization(self):
        """Test that set objects are properly serialized to lists."""
        test_set = {1, 2, 3, 4}
        test_data = {"numbers": test_set, "type": "set"}

        result = dumps_message(test_data)
        parsed = json.loads(result)

        # Sets are unordered, so we need to check contents
        assert set(parsed["numbers"]) == test_set
        assert parsed["type"] == "set"

    def test_bytes_utf8_serialization(self):
        """Test that UTF-8 bytes are properly serialized to strings."""
        test_bytes = "hello world".encode("utf-8")
        test_data = {"message": test_bytes, "encoding": "utf-8"}

        result = dumps_message(test_data)
        parsed = json.loads(result)

        assert parsed["message"] == "hello world"
        assert parsed["encoding"] == "utf-8"

    def test_bytes_base64_serialization(self):
        """Test that non-UTF-8 bytes are properly serialized to base64."""
        test_bytes = b"\x89\x50\x4e\x47"  # PNG header bytes
        test_data = {"data": test_bytes, "type": "binary"}

        result = dumps_message(test_data)
        parsed = json.loads(result)

        # Should be base64 encoded
        import base64

        expected = base64.b64encode(test_bytes).decode("ascii")
        assert parsed["data"] == expected
        assert parsed["type"] == "binary"

    def test_mixed_types_serialization(self):
        """Test serialization of mixed data types in one message."""
        test_uuid = uuid.uuid4()
        test_datetime = datetime.datetime(2024, 1, 15, 10, 30, 45)
        test_decimal = decimal.Decimal("99.99")
        test_set = {"apple", "banana", "cherry"}

        test_data = {
            "id": test_uuid,
            "created_at": test_datetime,
            "price": test_decimal,
            "tags": test_set,
            "name": "Test Product",
        }

        result = dumps_message(test_data)
        parsed = json.loads(result)

        assert parsed["id"] == str(test_uuid)
        assert parsed["created_at"] == "2024-01-15T10:30:45"
        assert parsed["price"] == 99.99
        assert set(parsed["tags"]) == test_set
        assert parsed["name"] == "Test Product"

    def test_standard_types_unchanged(self):
        """Test that standard JSON types are serialized normally."""
        test_data = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }

        result = dumps_message(test_data)
        parsed = json.loads(result)

        assert parsed == test_data

    def test_loads_message_function(self):
        """Test the loads_message convenience function."""
        test_data = {"id": str(uuid.uuid4()), "name": "test"}
        json_string = json.dumps(test_data)

        result = loads_message(json_string)

        assert result == test_data

    def test_unsupported_type_raises_error(self):
        """Test that unsupported types raise TypeError."""

        class CustomObject:
            pass

        test_data = {"custom": CustomObject()}

        with pytest.raises(TypeError):
            dumps_message(test_data)
