"""
Settings API Endpoint Tests
Tests for provider settings CRUD operations
"""
import pytest
from httpx import AsyncClient


class TestSettingsAPI:
    """Test Settings API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_settings(self, client: AsyncClient, sample_settings_data):
        """Test creating provider settings"""
        response = await client.post("/api/v1/settings", json=sample_settings_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["provider"] == sample_settings_data["provider"]
        assert data["is_active"] == sample_settings_data["is_active"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_duplicate_settings(self, client: AsyncClient, sample_settings_data):
        """Test creating duplicate settings returns 409"""
        # Create first
        await client.post("/api/v1/settings", json=sample_settings_data)
        
        # Try to create duplicate
        response = await client.post("/api/v1/settings", json=sample_settings_data)
        assert response.status_code == 409
    
    @pytest.mark.asyncio
    async def test_list_settings(self, client: AsyncClient, sample_settings_data):
        """Test listing all settings"""
        # Create settings
        await client.post("/api/v1/settings", json=sample_settings_data)
        
        # List settings
        response = await client.get("/api/v1/settings")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["provider"] == sample_settings_data["provider"]
    
    @pytest.mark.asyncio
    async def test_get_settings_by_id(self, client: AsyncClient, sample_settings_data):
        """Test getting settings by ID"""
        # Create settings
        create_response = await client.post("/api/v1/settings", json=sample_settings_data)
        settings_id = create_response.json()["id"]
        
        # Get by ID
        response = await client.get(f"/api/v1/settings/{settings_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == settings_id
        assert data["provider"] == sample_settings_data["provider"]
    
    @pytest.mark.asyncio
    async def test_get_settings_by_provider(self, client: AsyncClient, sample_settings_data):
        """Test getting settings by provider name"""
        # Create settings
        await client.post("/api/v1/settings", json=sample_settings_data)
        
        # Get by provider
        response = await client.get(f"/api/v1/settings/provider/{sample_settings_data['provider']}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["provider"] == sample_settings_data["provider"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_settings(self, client: AsyncClient):
        """Test getting non-existent settings returns 404"""
        response = await client.get("/api/v1/settings/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_settings(self, client: AsyncClient, sample_settings_data):
        """Test updating settings"""
        # Create settings
        create_response = await client.post("/api/v1/settings", json=sample_settings_data)
        settings_id = create_response.json()["id"]
        
        # Update settings
        update_data = {"is_active": False}
        response = await client.put(f"/api/v1/settings/{settings_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_delete_settings(self, client: AsyncClient, sample_settings_data):
        """Test deleting settings"""
        # Create settings
        create_response = await client.post("/api/v1/settings", json=sample_settings_data)
        settings_id = create_response.json()["id"]
        
        # Delete settings
        response = await client.delete(f"/api/v1/settings/{settings_id}")
        assert response.status_code == 204
        
        # Verify deleted
        get_response = await client.get(f"/api/v1/settings/{settings_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_activate_settings(self, client: AsyncClient, sample_settings_data):
        """Test activating settings"""
        # Create inactive settings
        sample_settings_data["is_active"] = False
        create_response = await client.post("/api/v1/settings", json=sample_settings_data)
        settings_id = create_response.json()["id"]
        
        # Activate
        response = await client.post(f"/api/v1/settings/{settings_id}/activate")
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_deactivate_settings(self, client: AsyncClient, sample_settings_data):
        """Test deactivating settings"""
        # Create active settings
        create_response = await client.post("/api/v1/settings", json=sample_settings_data)
        settings_id = create_response.json()["id"]
        
        # Deactivate
        response = await client.post(f"/api/v1/settings/{settings_id}/deactivate")
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_list_active_only(self, client: AsyncClient, sample_settings_data):
        """Test listing only active settings"""
        # Create active settings
        await client.post("/api/v1/settings", json=sample_settings_data)
        
        # Create inactive settings
        inactive_data = sample_settings_data.copy()
        inactive_data["provider"] = "OPENAI"
        inactive_data["is_active"] = False
        await client.post("/api/v1/settings", json=inactive_data)
        
        # List active only
        response = await client.get("/api/v1/settings?active_only=true")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_active"] is True
