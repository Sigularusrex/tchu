import pytest
from tchu.utils.retry_decorator import run_with_retries

def test_retry_decorator_success():
    attempts = 0
    
    @run_with_retries
    def test_function(self):
        nonlocal attempts
        attempts += 1
        return "success"
    
    result = test_function(None)
    assert result == "success"
    assert attempts == 1

def test_retry_decorator_failure():
    attempts = 0
    
    @run_with_retries
    def test_function(self):
        nonlocal attempts
        attempts += 1
        raise Exception("Test error")
    
    with pytest.raises(ConnectionError):
        test_function(None)
    assert attempts == 10  # Max attempts 