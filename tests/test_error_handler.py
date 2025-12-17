"""Tests for ErrorHandler class."""

import pytest
import json
from pathlib import Path
from src.utils.error_handler import ErrorHandler, ErrorSeverity


@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file for testing."""
    log_file = tmp_path / "test_errors.log"
    ErrorHandler._initialized = False  # Reset for each test
    ErrorHandler.initialize(str(log_file))
    yield log_file
    # Cleanup
    if log_file.exists():
        log_file.unlink()


def test_error_handler_initialization(temp_log_file):
    """Test that ErrorHandler initializes correctly."""
    assert ErrorHandler._initialized is True
    assert ErrorHandler._log_file == temp_log_file
    assert ErrorHandler._error_count == 0
    assert ErrorHandler._critical_count == 0


def test_log_silent_creates_log_entry(temp_log_file):
    """Test that log_silent writes to log file."""
    test_error = ValueError("Test error")
    ErrorHandler.log_silent(test_error, "Test context")
    
    # Read log file
    assert temp_log_file.exists()
    with open(temp_log_file, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 1
    log_entry = json.loads(lines[0])
    
    assert log_entry["level"] == "SILENT"
    assert log_entry["context"] == "Test context"
    assert log_entry["message"] == "Test error"
    assert log_entry["exception"] == "ValueError"


def test_log_info_creates_log_entry(temp_log_file):
    """Test that log_info writes to log file."""
    ErrorHandler.log_info("Test info message", "Test context")
    
    # Read log file
    with open(temp_log_file, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 1
    log_entry = json.loads(lines[0])
    
    assert log_entry["level"] == "INFO"
    assert log_entry["context"] == "Test context"
    assert log_entry["message"] == "Test info message"


def test_error_counting(temp_log_file):
    """Test that error count increments correctly."""
    assert ErrorHandler.get_error_count() == 0
    
    # Log a silent error
    ErrorHandler.log_silent(ValueError("Test"), "Context")
    assert ErrorHandler.get_error_count() == 1
    
    # Log another
    ErrorHandler.log_silent(ValueError("Test 2"), "Context 2")
    assert ErrorHandler.get_error_count() == 2


def test_critical_error_counting(temp_log_file):
    """Test that critical errors are counted separately."""
    assert ErrorHandler.get_critical_count() == 0
    
    # This would show a dialog in real usage, but we're just testing the counting
    # We'll mock the messagebox in a separate test
    ErrorHandler._log_error_internal(
        ValueError("Critical test"),
        "Test context",
        ErrorSeverity.CRITICAL
    )
    ErrorHandler._increment_error_count(ErrorSeverity.CRITICAL)
    
    assert ErrorHandler.get_error_count() == 1
    assert ErrorHandler.get_critical_count() == 1


def test_clear_error_count(temp_log_file):
    """Test that error count can be cleared."""
    ErrorHandler.log_silent(ValueError("Test"), "Context")
    assert ErrorHandler.get_error_count() == 1
    
    ErrorHandler.clear_error_count()
    assert ErrorHandler.get_error_count() == 0
    assert ErrorHandler.get_critical_count() == 0


def test_get_recent_errors(temp_log_file):
    """Test retrieving recent errors from log."""
    # Log some errors
    ErrorHandler.log_silent(ValueError("Error 1"), "Context 1")
    ErrorHandler.log_silent(ValueError("Error 2"), "Context 2")
    ErrorHandler.log_info("Info message", "Context 3")
    
    # Get recent errors
    errors = ErrorHandler.get_recent_errors(limit=10)
    
    assert len(errors) == 3
    assert errors[0]["message"] == "Error 1"
    assert errors[1]["message"] == "Error 2"
    assert errors[2]["message"] == "Info message"


def test_get_recent_errors_with_limit(temp_log_file):
    """Test that limit parameter works correctly."""
    # Log 5 errors
    for i in range(5):
        ErrorHandler.log_silent(ValueError(f"Error {i}"), f"Context {i}")
    
    # Get only last 2
    errors = ErrorHandler.get_recent_errors(limit=2)
    
    assert len(errors) == 2
    assert errors[0]["message"] == "Error 3"
    assert errors[1]["message"] == "Error 4"


def test_error_callback(temp_log_file):
    """Test that error callback is called when errors occur."""
    callback_calls = []
    
    def test_callback(count, color):
        callback_calls.append((count, color))
    
    ErrorHandler.set_error_callback(test_callback)
    
    # Log a silent error
    ErrorHandler.log_silent(ValueError("Test"), "Context")
    
    assert len(callback_calls) == 1
    assert callback_calls[0] == (1, "orange")


def test_critical_error_callback_color(temp_log_file):
    """Test that critical errors trigger red badge color."""
    callback_calls = []
    
    def test_callback(count, color):
        callback_calls.append((count, color))
    
    ErrorHandler.set_error_callback(test_callback)
    
    # Simulate critical error (without showing dialog)
    ErrorHandler._log_error_internal(
        ValueError("Critical"),
        "Context",
        ErrorSeverity.CRITICAL
    )
    ErrorHandler._increment_error_count(ErrorSeverity.CRITICAL)
    
    assert len(callback_calls) == 1
    assert callback_calls[0] == (1, "red")
