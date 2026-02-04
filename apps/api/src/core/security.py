"""
Security Layer - Secret Management and Encryption
Uses Fernet symmetric encryption for secrets at rest
"""
from cryptography.fernet import Fernet
from typing import Optional
import base64
import hashlib
import secrets
from datetime import datetime


class SecretManager:
    """
    Manages encryption/decryption of secrets (API keys, tokens).
    Uses Fernet (symmetric encryption) with key derived from SECRET_KEY.
    
    Security considerations:
    - Secrets are encrypted at rest in database
    - Encryption key stored in environment (not in code/repo)
    - Support for key rotation (future enhancement)
    - Audit logging for secret access
    """
    
    def __init__(self, secret_key: str):
        """
        Initialize with base secret key.
        
        Args:
            secret_key: Base secret key from environment (min 32 bytes recommended)
        """
        # Derive Fernet key from secret_key using SHA256
        # Fernet requires 32 url-safe base64-encoded bytes
        key_hash = hashlib.sha256(secret_key.encode()).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(key_hash))
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a secret value.
        
        Args:
            plaintext: Plain text secret to encrypt
            
        Returns:
            Base64-encoded encrypted value (safe for database storage)
        """
        if not plaintext:
            return ""
        
        encrypted_bytes = self._fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()  # Store as string
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt a secret value.
        
        Args:
            encrypted: Encrypted value from database
            
        Returns:
            Decrypted plaintext
            
        Raises:
            ValueError: If decryption fails (invalid token/key)
        """
        if not encrypted:
            return ""
        
        try:
            decrypted_bytes = self._fernet.decrypt(encrypted.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            # Log this - it indicates tampered data or wrong key
            raise ValueError(f"Failed to decrypt secret: {str(e)}")
    
    def is_encrypted(self, value: str) -> bool:
        """
        Check if a value is encrypted (heuristic).
        Fernet tokens start with 'gAAAAA' after base64 encoding.
        
        Args:
            value: Value to check
            
        Returns:
            True if likely encrypted, False otherwise
        """
        if not value or len(value) < 20:
            return False
        
        # Fernet tokens have specific structure
        try:
            # Try to decrypt - if it works, it's encrypted
            self._fernet.decrypt(value.encode())
            return True
        except:
            return False
    
    def rotate_key(self, old_key: str, new_key: str, encrypted_value: str) -> str:
        """
        Rotate encryption key for a secret.
        Decrypts with old key, re-encrypts with new key.
        
        Args:
            old_key: Previous secret key
            new_key: New secret key
            encrypted_value: Value encrypted with old key
            
        Returns:
            Value re-encrypted with new key
        """
        # Decrypt with old key
        old_manager = SecretManager(old_key)
        plaintext = old_manager.decrypt(encrypted_value)
        
        # Re-encrypt with new key
        new_manager = SecretManager(new_key)
        return new_manager.encrypt(plaintext)


class AuditLogger:
    """
    Audit logging for security-sensitive operations.
    Tracks who accessed what secrets when.
    
    For MVP: Simple in-memory logging
    For Production: Persist to database or external audit service
    """
    
    def __init__(self):
        self._logs: list[dict] = []
    
    def log_secret_access(
        self,
        operation: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        success: bool = True
    ):
        """
        Log a security-sensitive operation.
        
        Args:
            operation: Type of operation (encrypt, decrypt, rotate)
            user_id: User performing operation (optional for MVP)
            resource: Resource identifier (e.g., settings_id)
            success: Whether operation succeeded
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "user_id": user_id,
            "resource": resource,
            "success": success
        }
        self._logs.append(log_entry)
        
        # TODO: For production, persist to database or send to SIEM
        # For now, just keep in memory (will be lost on restart)
    
    def get_logs(self, limit: int = 100) -> list[dict]:
        """Get recent audit logs"""
        return self._logs[-limit:]


# Global instances (initialized with config at startup)
_secret_manager: Optional[SecretManager] = None
_audit_logger = AuditLogger()


def init_security(secret_key: str):
    """
    Initialize security layer with secret key.
    Called once at application startup.
    
    Args:
        secret_key: Base secret key from configuration
    """
    global _secret_manager
    _secret_manager = SecretManager(secret_key)


def get_secret_manager() -> SecretManager:
    """Get the global secret manager instance"""
    if _secret_manager is None:
        raise RuntimeError("Security not initialized. Call init_security() first.")
    return _secret_manager


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    return _audit_logger


def generate_secret_key() -> str:
    """
    Generate a secure random secret key for Fernet.
    Use this to generate new SECRET_KEY for .env file.
    
    Returns:
        32-byte hex string suitable for SECRET_KEY
    """
    return secrets.token_hex(32)  # 256 bits


# Convenience exports
secret_manager = get_secret_manager
audit_logger = get_audit_logger
