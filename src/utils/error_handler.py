"""
Centralized error handling with severity-based notifications.

This module provides the ErrorHandler class for managing all application errors
with appropriate logging, user notifications, and badge updates.
"""

import json
import logging
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, List, Dict
from tkinter import messagebox


class ErrorSeverity(Enum):
    """Error severity levels determining user notification behavior."""
    CRITICAL = "critical"    # Show dialog + red badge + log
    ERROR = "error"          # Show dialog + orange badge + log
    WARNING = "warning"      # Show dialog + log (validation)
    INFO = "info"            # Show dialog only (no badge, no log)
    SILENT = "silent"        # Log only + orange badge (no dialog)


class ErrorHandler:
    """
    Centralized error handling with severity-based notifications.
    
    Features:
    - Severity-based error handling (CRITICAL, ERROR, WARNING, INFO, SILENT)
    - Logs errors to rotating log file
    - Shows user-friendly dialogs for important errors
    - Tracks error count with color-coded badge
    - Provides error log viewer data
    - Silent logging for non-critical errors
    """
    
    # Class variables
    _log_file = None
    _error_count = 0
    _critical_count = 0
    _error_callback = None
    _logger = None
    _initialized = False
    
    @classmethod
    def initialize(cls, log_file: str = "app_errors.log"):
        """
        Initialize the error handler with log file.
        
        Args:
            log_file: Path to log file (default: app_errors.log in current directory)
        """
        if cls._initialized:
            return
        
        cls._log_file = Path(log_file)
        cls._error_count = 0
        cls._critical_count = 0
        cls._initialized = True
    
    # ============ Main Error Handling ============
    
    @classmethod
    def handle_error(
        cls,
        error: Exception,
        user_message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: str = "",
        details: Optional[str] = None
    ):
        """
        Handle error based on severity level.
        
        Args:
            error: The exception that occurred
            user_message: User-friendly error message
            severity: Error severity level
            context: Context information (e.g., "Renaming song 12345")
            details: Additional details to show in dialog
            
        Behavior by severity:
            CRITICAL: Show dialog + red badge + log
            ERROR: Show dialog + orange badge + log
            WARNING: Show dialog + log
            INFO: Show dialog only (no badge, no log)
            SILENT: Log only + orange badge (no dialog)
        """
        # Ensure initialized
        if not cls._initialized:
            cls.initialize()
        
        # Log the error (except INFO)
        if severity != ErrorSeverity.INFO:
            cls._log_error_internal(error, context, severity)
        
        # Update badge (except INFO)
        if severity != ErrorSeverity.INFO:
            cls._increment_error_count(severity)
        
        # Show dialog (except SILENT)
        if severity != ErrorSeverity.SILENT:
            if severity == ErrorSeverity.CRITICAL:
                messagebox.showerror(
                    "Critical Error",
                    user_message + (f"\n\nDetails: {details}" if details else "")
                )
            elif severity == ErrorSeverity.ERROR:
                messagebox.showerror(
                    "Error",
                    user_message + (f"\n\nDetails: {details}" if details else "")
                )
            elif severity == ErrorSeverity.WARNING:
                messagebox.showwarning("Warning", user_message)
            elif severity == ErrorSeverity.INFO:
                messagebox.showinfo("Info", user_message)
    
    # ============ Convenience Methods ============
    
    @classmethod
    def show_critical(cls, message: str, details: Optional[str] = None):
        """Show critical error dialog and log."""
        cls.handle_error(
            Exception(message),
            message,
            ErrorSeverity.CRITICAL,
            details=details
        )
    
    @classmethod
    def show_error(cls, message: str, details: Optional[str] = None):
        """Show error dialog and log."""
        cls.handle_error(
            Exception(message),
            message,
            ErrorSeverity.ERROR,
            details=details
        )
    
    @classmethod
    def show_warning(cls, message: str):
        """Show warning dialog and log."""
        cls.handle_error(
            Exception(message),
            message,
            ErrorSeverity.WARNING
        )
    
    @classmethod
    def show_info(cls, message: str):
        """Show info dialog (no logging)."""
        cls.handle_error(
            Exception(message),
            message,
            ErrorSeverity.INFO
        )
    
    @classmethod
    def log_silent(cls, error: Exception, context: str = ""):
        """Log error silently without showing dialog."""
        cls.handle_error(
            error,
            str(error),
            ErrorSeverity.SILENT,
            context=context
        )
    
    @staticmethod
    def ask_yes_no(message: str, title: str = "Confirm") -> bool:
        """Show yes/no dialog and return user choice."""
        return messagebox.askyesno(title, message)
    
    # ============ Logging Methods ============
    
    @classmethod
    def _log_error_internal(cls, error: Exception, context: str, severity: ErrorSeverity):
        """Internal method to log error to file."""
        if not cls._log_file:
            return
        
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": severity.value.upper(),
            "context": context,
            "message": str(error),
            "exception": type(error).__name__,
            "stack_trace": traceback.format_exc() if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR] else None
        }
        
        # Append to log file (JSON Lines format)
        try:
            with open(cls._log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            # If logging fails, print to console as fallback
            print(f"Failed to write to log file: {e}")
            print(f"Original error: {error}")
    
    @classmethod
    def log_info(cls, message: str, context: str = ""):
        """Log info message (no dialog, no badge)."""
        if not cls._initialized:
            cls.initialize()
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "context": context,
            "message": message,
            "exception": None,
            "stack_trace": None
        }
        
        try:
            with open(cls._log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Failed to write to log file: {e}")
    
    # ============ Badge Management ============
    
    @classmethod
    def _increment_error_count(cls, severity: ErrorSeverity):
        """Increment error count and update badge."""
        cls._error_count += 1
        if severity == ErrorSeverity.CRITICAL:
            cls._critical_count += 1
        
        if cls._error_callback:
            # Determine badge color based on severity
            badge_color = "red" if cls._critical_count > 0 else "orange"
            cls._error_callback(cls._error_count, badge_color)
    
    @classmethod
    def get_error_count(cls) -> int:
        """Get count of errors since app started."""
        return cls._error_count
    
    @classmethod
    def get_critical_count(cls) -> int:
        """Get count of critical errors."""
        return cls._critical_count
    
    @classmethod
    def clear_error_count(cls):
        """Reset error count (after user views log)."""
        cls._error_count = 0
        cls._critical_count = 0
        if cls._error_callback:
            cls._error_callback(0, "normal")
    
    @classmethod
    def set_error_callback(cls, callback: Callable[[int, str], None]):
        """
        Set callback to update UI badge when errors occur.
        
        Args:
            callback: Function(error_count: int, badge_color: str)
        """
        cls._error_callback = callback
    
    # ============ Error Log Viewer ============
    
    @classmethod
    def get_recent_errors(cls, limit: int = 50) -> List[Dict]:
        """
        Get recent errors for log viewer.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of error dictionaries
        """
        # Ensure initialized
        if not cls._initialized:
            cls.initialize()
            
        if not cls._log_file or not cls._log_file.exists():
            return []
        
        errors = []
        try:
            with open(cls._log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Get last N lines
                for line in lines[-limit:]:
                    try:
                        errors.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Failed to read log file: {e}")
            # Return a fake error so the user knows reading failed
            return [{
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR", 
                "context": "System",
                "message": f"Failed to read log file: {e}",
                "exception": "IOError"
            }]
        
        return errors

    @classmethod
    def clear_log_file(cls):
        """Clear the error log file."""
        if not cls._log_file:
            return
        try:
            with open(cls._log_file, 'w', encoding='utf-8') as f:
                f.write("")
        except Exception:
            pass
