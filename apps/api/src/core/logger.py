"""
Structured Logging - JSON Logging with Sensitive Data Sanitization
Provides contextual logging with automatic secret masking
"""
import logging
import json
import sys
from typing import Any, Optional
from datetime import datetime
from pathlib import Path


class SanitizingFilter(logging.Filter):
    """
    Logging filter that sanitizes sensitive data.
    Masks API keys, tokens, and other secrets in log messages.
    """
    
    # Patterns to redact (case-insensitive)
    SENSITIVE_KEYS = {
        "api_key", "apikey", "token", "secret", "password", 
        "authorization", "auth", "key", "credential"
    }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Sanitize log record before output.
        
        Args:
            record: Log record to sanitize
            
        Returns:
            True (always allow the record through after sanitization)
        """
        # Sanitize message
        if isinstance(record.msg, str):
            record.msg = self._mask_secrets(record.msg)
        
        # Sanitize args (if dict/list)
        if record.args:
            if isinstance(record.args, dict):
                record.args = self._sanitize_dict(record.args)
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(self._mask_secrets(str(arg)) for arg in record.args)
        
        return True
    
    def _mask_secrets(self, text: str) -> str:
        """
        Mask secrets in text using heuristics.
        
        Args:
            text: Text that may contain secrets
            
        Returns:
            Text with secrets masked
        """
        # Simple heuristic: Look for patterns like "key=value" or "key: value"
        for key in self.SENSITIVE_KEYS:
            # Pattern: key=sk-... or key="sk-..." or key: sk-...
            import re
            # Match key followed by = or : and then capture value
            pattern = rf'({key}["\']?\s*[:=]\s*["\']?)([^\s,\}}\]]+)'
            text = re.sub(
                pattern,
                r'\1***REDACTED***',
                text,
                flags=re.IGNORECASE
            )
        
        return text
    
    def _sanitize_dict(self, data: dict) -> dict:
        """
        Recursively sanitize dictionary values.
        
        Args:
            data: Dictionary that may contain sensitive data
            
        Returns:
            Dictionary with sensitive values masked
        """
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, (list, tuple)):
                sanitized[key] = [
                    self._sanitize_dict(v) if isinstance(v, dict) else v
                    for v in value
                ]
            else:
                sanitized[key] = value
        return sanitized


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    Outputs logs as JSON for easy parsing by log aggregation systems.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra context (if provided)
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        # Add run_id for workflow tracing (if present)
        if hasattr(record, "run_id"):
            log_data["run_id"] = record.run_id
        
        # Add user_id for audit tracing (if present)
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development.
    """
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ("json" or "text")
        log_file: Optional file path for log output
        
    Returns:
        Configured root logger
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Add sanitizing filter
    sanitizing_filter = SanitizingFilter()
    console_handler.addFilter(sanitizing_filter)
    
    # Set formatter
    if log_format == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(TextFormatter())
    
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.addFilter(sanitizing_filter)
        
        # Always use JSON for file logs (easier to parse)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    
    return logger


class ContextualLogger:
    """
    Logger with automatic context injection.
    Useful for adding run_id, user_id to all log messages.
    """
    
    def __init__(
        self,
        name: str,
        run_id: Optional[str] = None,
        user_id: Optional[str] = None,
        extra_context: Optional[dict[str, Any]] = None
    ):
        """
        Args:
            name: Logger name (usually __name__)
            run_id: Run ID for workflow tracing
            user_id: User ID for audit tracing
            extra_context: Additional context to include in all logs
        """
        self.logger = logging.getLogger(name)
        self.run_id = run_id
        self.user_id = user_id
        self.extra_context = extra_context or {}
    
    def _add_context(self, extra: Optional[dict] = None) -> dict:
        """Add contextual information to log extra"""
        context = self.extra_context.copy()
        if self.run_id:
            context["run_id"] = self.run_id
        if self.user_id:
            context["user_id"] = self.user_id
        if extra:
            context.update(extra)
        return {"context": context} if context else {}
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context"""
        self.logger.debug(message, extra=self._add_context(kwargs))
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, extra=self._add_context(kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, extra=self._add_context(kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.error(message, extra=self._add_context(kwargs))
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context"""
        self.logger.critical(message, extra=self._add_context(kwargs))
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback and context"""
        self.logger.exception(message, extra=self._add_context(kwargs))


def get_logger(
    name: str,
    run_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **context
) -> ContextualLogger:
    """
    Get a contextual logger instance.
    
    Args:
        name: Logger name (usually __name__)
        run_id: Run ID for workflow tracing
        user_id: User ID for audit tracing
        **context: Additional context to include
        
    Returns:
        ContextualLogger instance
    """
    return ContextualLogger(
        name=name,
        run_id=run_id,
        user_id=user_id,
        extra_context=context
    )
