"""
Settings Service - Provider Configuration Management
Handles CRUD operations for provider settings with encryption
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Settings as SettingsModel, Provider
from db.repositories import SettingsRepository
from models.schemas import (
    SettingsCreate,
    SettingsUpdate,
    SettingsResponse
)
from core import (
    get_secret_manager,
    get_audit_logger,
    SettingsNotFoundError,
    DuplicateSettingsError,
    DecryptionError,
    ProviderAuthenticationError,
    get_logger
)
from providers import get_provider


class SettingsService:
    """
    Service for managing provider settings.
    
    Responsibilities:
    - Encrypt API keys before storage
    - Decrypt API keys for use
    - Validate API keys against provider
    - Track settings status (tested, active)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = SettingsRepository(session)
        self.secret_manager = get_secret_manager()
        self.audit_logger = get_audit_logger()
        self.logger = get_logger(__name__)
    
    async def create_settings(self, data: SettingsCreate) -> SettingsResponse:
        """
        Create new provider settings.
        
        Args:
            data: Settings creation data
            
        Returns:
            Created settings (with encrypted API key)
            
        Raises:
            DuplicateSettingsError: If settings already exist for provider
            ValidationError: If API key validation fails
        """
        # Check if settings already exist
        existing = await self.repository.get_by_provider(data.provider)
        if existing:
            raise DuplicateSettingsError(data.provider.value)
        
        # Encrypt API key
        self.logger.info(f"Creating settings for provider: {data.provider.value}")
        encrypted_key = self.secret_manager.encrypt(data.api_key)
        
        # Log the operation
        self.audit_logger.log_secret_access(
            operation="encrypt",
            resource=f"settings:{data.provider.value}",
            success=True
        )
        
        # Create settings in database
        settings = await self.repository.create(
            provider=data.provider,
            encrypted_value=encrypted_key,
            is_active=data.is_active
        )
        
        self.logger.info(f"Settings created for {data.provider.value} with ID: {settings.id}")
        
        return SettingsResponse.model_validate(settings)
    
    async def get_settings(self, settings_id: str) -> SettingsResponse:
        """Get settings by ID"""
        settings = await self.repository.get(settings_id)
        if not settings:
            raise SettingsNotFoundError(settings_id)
        
        return SettingsResponse.model_validate(settings)
    
    async def get_settings_by_provider(self, provider: Provider) -> Optional[SettingsResponse]:
        """Get settings for a specific provider"""
        settings = await self.repository.get_by_provider(provider)
        if not settings:
            return None
        
        return SettingsResponse.model_validate(settings)
    
    async def list_settings(
        self,
        active_only: bool = False,
        tested_only: bool = False
    ) -> list[SettingsResponse]:
        """
        List all provider settings.
        
        Args:
            active_only: Return only active settings
            tested_only: Return only tested settings
            
        Returns:
            List of settings
        """
        all_settings = await self.repository.get_all()
        
        # Apply filters
        filtered = all_settings
        if active_only:
            filtered = [s for s in filtered if s.is_active]
        if tested_only:
            filtered = [s for s in filtered if s.test_status == "success"]
        
        return [SettingsResponse.model_validate(s) for s in filtered]
    
    async def update_settings(
        self,
        settings_id: str,
        data: SettingsUpdate
    ) -> SettingsResponse:
        """
        Update provider settings.
        
        Args:
            settings_id: Settings ID
            data: Update data
            
        Returns:
            Updated settings
        """
        settings = await self.repository.get(settings_id)
        if not settings:
            raise SettingsNotFoundError(settings_id)
        
        update_dict = data.model_dump(exclude_unset=True)
        
        # If API key is being updated, encrypt it
        if "api_key" in update_dict:
            new_key = update_dict.pop("api_key")
            update_dict["encrypted_value"] = self.secret_manager.encrypt(new_key)
            update_dict["is_tested"] = False  # Re-test required
            
            self.audit_logger.log_secret_access(
                operation="update_encrypt",
                resource=f"settings:{settings.id}",
                success=True
            )
        
        # Update settings
        updated = await self.repository.update(settings_id, **update_dict)
        
        self.logger.info(f"Settings updated for ID: {settings_id}")
        
        return SettingsResponse.model_validate(updated)
    
    async def delete_settings(self, settings_id: str) -> bool:
        """
        Delete provider settings.
        
        Args:
            settings_id: Settings ID
            
        Returns:
            True if deleted
        """
        settings = await self.repository.get(settings_id)
        if not settings:
            raise SettingsNotFoundError(settings_id)
        
        await self.repository.delete(settings_id)
        
        self.logger.info(f"Settings deleted for ID: {settings_id}")
        self.audit_logger.log_secret_access(
            operation="delete",
            resource=f"settings:{settings_id}",
            success=True
        )
        
        return True
    
    async def test_api_key(self, settings_id: str) -> bool:
        """
        Test API key against provider.
        
        Args:
            settings_id: Settings ID
            
        Returns:
            True if API key is valid
            
        Raises:
            ProviderAuthenticationError: If API key is invalid
            DecryptionError: If decryption fails
        """
        settings = await self.repository.get(settings_id)
        if not settings:
            raise SettingsNotFoundError(settings_id)
        
        try:
            # Decrypt API key
            api_key = self.secret_manager.decrypt(settings.encrypted_value)
            
            self.audit_logger.log_secret_access(
                operation="decrypt_test",
                resource=f"settings:{settings.id}",
                success=True
            )
            
            # Validate with provider
            provider = get_provider(
                settings.provider.value,
                api_key,
                timeout=10
            )
            
            self.logger.info(f"Testing API key for provider: {settings.provider.value}")
            is_valid = await provider.validate_api_key(api_key)
            
            if is_valid:
                # Mark as tested
                from datetime import datetime
                await self.repository.mark_tested(
                    provider=settings.provider,
                    success=True,
                    tested_at=datetime.utcnow()
                )
                self.logger.info(f"API key test successful for {settings.provider.value}")
                return True
            else:
                raise ProviderAuthenticationError(settings.provider.value)
                
        except ValueError as e:
            self.logger.error(f"Decryption failed for settings {settings_id}")
            raise DecryptionError()
    
    async def test_settings(self, settings_id: str):
        """
        Test provider settings and return detailed response.
        
        Args:
            settings_id: Settings ID
            
        Returns:
            SettingsTestResponse with test results
        """
        from datetime import datetime
        from models.schemas import SettingsTestResponse
        
        settings = await self.repository.get(settings_id)
        if not settings:
            raise SettingsNotFoundError(settings_id)
        
        try:
            # Decrypt API key
            api_key = self.secret_manager.decrypt(settings.encrypted_value)
            
            self.audit_logger.log_secret_access(
                operation="decrypt_test",
                resource=f"settings:{settings.id}",
                success=True
            )
            
            # Validate with provider
            provider = get_provider(
                settings.provider.value,
                api_key,
                timeout=10
            )
            
            self.logger.info(f"Testing API key for provider: {settings.provider.value}")
            is_valid = await provider.validate_api_key(api_key)
            
            tested_at = datetime.utcnow()
            
            if is_valid:
                # Mark as tested
                await self.repository.mark_tested(
                    provider=settings.provider,
                    success=True,
                    tested_at=tested_at
                )
                self.logger.info(f"API key test successful for {settings.provider.value}")
                
                return SettingsTestResponse(
                    success=True,
                    message=f"{settings.provider.value} API key is valid",
                    provider=settings.provider.value,
                    tested_at=tested_at
                )
            else:
                await self.repository.mark_tested(
                    provider=settings.provider,
                    success=False,
                    tested_at=tested_at
                )
                return SettingsTestResponse(
                    success=False,
                    message=f"{settings.provider.value} API key is invalid",
                    provider=settings.provider.value,
                    tested_at=tested_at
                )
                
        except ProviderAuthenticationError:
            tested_at = datetime.utcnow()
            await self.repository.mark_tested(
                provider=settings.provider,
                success=False,
                tested_at=tested_at
            )
            return SettingsTestResponse(
                success=False,
                message=f"Authentication failed for {settings.provider.value}",
                provider=settings.provider.value,
                tested_at=tested_at
            )
        except ValueError as e:
            self.logger.error(f"Decryption failed for settings {settings_id}")
            raise DecryptionError()
        except Exception as e:
            self.logger.error(f"Unexpected error testing settings: {str(e)}")
            tested_at = datetime.utcnow()
            return SettingsTestResponse(
                success=False,
                message=f"Test failed: {str(e)}",
                provider=settings.provider.value,
                tested_at=tested_at
            )
    
    async def activate_settings(self, settings_id: str) -> SettingsResponse:
        """Activate provider settings"""
        settings = await self.repository.get(settings_id)
        if not settings:
            raise SettingsNotFoundError(settings_id)
        
        updated = await self.repository.update(settings_id, is_active=True)
        self.logger.info(f"Settings activated for {settings.provider.value}")
        
        return SettingsResponse.model_validate(updated)
    
    async def deactivate_settings(self, settings_id: str) -> SettingsResponse:
        """Deactivate provider settings"""
        settings = await self.repository.get(settings_id)
        if not settings:
            raise SettingsNotFoundError(settings_id)
        
        updated = await self.repository.deactivate(settings_id)
        self.logger.info(f"Settings deactivated for {settings.provider.value}")
        
        return SettingsResponse.model_validate(updated)
    
    async def get_decrypted_api_key(self, settings_id: str) -> str:
        """
        Get decrypted API key for internal use.
        
        Args:
            settings_id: Settings ID
            
        Returns:
            Decrypted API key
            
        Note:
            This method should only be used by internal services (workflow engine).
            Never expose decrypted keys to API endpoints.
        """
        settings = await self.repository.get(settings_id)
        if not settings:
            raise SettingsNotFoundError(settings_id)
        
        try:
            api_key = self.secret_manager.decrypt(settings.encrypted_value)
            
            self.audit_logger.log_secret_access(
                operation="decrypt",
                resource=f"settings:{settings.id}",
                success=True
            )
            
            return api_key
            
        except ValueError:
            raise DecryptionError()
