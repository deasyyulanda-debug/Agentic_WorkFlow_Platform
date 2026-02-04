"""
Custom Exceptions - Domain-Specific Error Handling
Maps business logic errors to HTTP status codes and user-friendly messages
"""
from typing import Optional, Any
from fastapi import status


class AppException(Exception):
    """
    Base application exception.
    All custom exceptions inherit from this for centralized handling.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[dict[str, Any]] = None
    ):
        """
        Args:
            message: User-friendly error message
            status_code: HTTP status code
            details: Additional context (dict for JSON response)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


# === Validation Errors (400) ===

class ValidationError(AppException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": field} if field else {}
        )


class InvalidWorkflowError(ValidationError):
    """Raised when workflow definition is invalid"""
    
    def __init__(self, message: str, workflow_id: Optional[str] = None):
        super().__init__(
            message=f"Invalid workflow: {message}",
        )
        if workflow_id:
            self.details["workflow_id"] = workflow_id


# === Not Found Errors (404) ===

class NotFoundError(AppException):
    """Raised when a resource is not found"""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier}
        )


class SettingsNotFoundError(NotFoundError):
    """Raised when provider settings not found"""
    
    def __init__(self, provider: str):
        super().__init__(resource="Provider settings", identifier=provider)


class WorkflowNotFoundError(NotFoundError):
    """Raised when workflow not found"""
    
    def __init__(self, workflow_id: str):
        super().__init__(resource="Workflow", identifier=workflow_id)


class RunNotFoundError(NotFoundError):
    """Raised when run not found"""
    
    def __init__(self, run_id: str):
        super().__init__(resource="Run", identifier=run_id)


# === Conflict Errors (409) ===

class ConflictError(AppException):
    """Raised when operation conflicts with current state"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT
        )


class DuplicateSettingsError(ConflictError):
    """Raised when trying to create duplicate provider settings"""
    
    def __init__(self, provider: str):
        super().__init__(
            message=f"Settings already exist for provider: {provider}"
        )


class InvalidStateTransitionError(ConflictError):
    """Raised when run state transition is invalid"""
    
    def __init__(self, current_state: str, target_state: str):
        super().__init__(
            message=f"Cannot transition from {current_state} to {target_state}"
        )


# === Provider Errors (502/503) ===

class ProviderError(AppException):
    """Base class for LLM provider errors"""
    
    def __init__(
        self,
        provider: str,
        message: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY
    ):
        super().__init__(
            message=f"{provider} error: {message}",
            status_code=status_code,
            details={"provider": provider}
        )


class ProviderAuthenticationError(ProviderError):
    """Raised when provider API key is invalid"""
    
    def __init__(self, provider: str):
        super().__init__(
            provider=provider,
            message="Invalid API key or authentication failed",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ProviderRateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded"""
    
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        super().__init__(
            provider=provider,
            message="Rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
        if retry_after:
            self.details["retry_after"] = retry_after


class ProviderTimeoutError(ProviderError):
    """Raised when provider request times out"""
    
    def __init__(self, provider: str):
        super().__init__(
            provider=provider,
            message="Request timed out",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT
        )


class ProviderResponseError(ProviderError):
    """Raised when provider returns invalid/unexpected response"""
    
    def __init__(self, provider: str, message: str):
        super().__init__(
            provider=provider,
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


# === Workflow Execution Errors (500) ===

class WorkflowExecutionError(AppException):
    """Raised when workflow execution fails"""
    
    def __init__(self, message: str, run_id: Optional[str] = None):
        super().__init__(
            message=f"Workflow execution failed: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        if run_id:
            self.details["run_id"] = run_id


class MaxIterationsExceededError(WorkflowExecutionError):
    """Raised when workflow exceeds max iterations (infinite loop protection)"""
    
    def __init__(self, max_iterations: int, run_id: Optional[str] = None):
        super().__init__(
            message=f"Maximum iterations exceeded: {max_iterations}",
            run_id=run_id
        )


class TokenLimitExceededError(WorkflowExecutionError):
    """Raised when workflow exceeds token limit (test-run mode)"""
    
    def __init__(self, token_limit: int, run_id: Optional[str] = None):
        super().__init__(
            message=f"Token limit exceeded: {token_limit}",
            run_id=run_id
        )


class TimeoutExceededError(WorkflowExecutionError):
    """Raised when workflow exceeds time limit (test-run mode)"""
    
    def __init__(self, timeout_seconds: int, run_id: Optional[str] = None):
        super().__init__(
            message=f"Execution timeout exceeded: {timeout_seconds}s",
            run_id=run_id
        )


# === Security Errors (403) ===

class SecurityError(AppException):
    """Base class for security-related errors"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class DecryptionError(SecurityError):
    """Raised when secret decryption fails"""
    
    def __init__(self):
        super().__init__(
            message="Failed to decrypt secret. Key may have been rotated or data corrupted."
        )


class EncryptionError(SecurityError):
    """Raised when secret encryption fails"""
    
    def __init__(self, message: str):
        super().__init__(
            message=f"Failed to encrypt secret: {message}"
        )


# === Database Errors ===

class DatabaseError(AppException):
    """Raised when database operation fails"""
    
    def __init__(self, message: str):
        super().__init__(
            message=f"Database error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
