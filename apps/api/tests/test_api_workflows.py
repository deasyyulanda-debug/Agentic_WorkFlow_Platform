"""
Workflows API Endpoint Tests
Tests for workflow CRUD operations
"""
import pytest
from httpx import AsyncClient


class TestWorkflowsAPI:
    """Test Workflows API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_workflow(self, client: AsyncClient, sample_workflow_data):
        """Test creating a workflow"""
        response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == sample_workflow_data["name"]
        assert data["persona"] == sample_workflow_data["persona"]
        assert data["is_active"] == sample_workflow_data["is_active"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_workflow_invalid_schema(self, client: AsyncClient, sample_workflow_data):
        """Test creating workflow with invalid schema"""
        invalid_data = sample_workflow_data.copy()
        invalid_data["invalid_field"] = {"invalid": "schema"}  # Use a truly invalid field
        
        response = await client.post("/api/v1/workflows", json=invalid_data)
        # FastAPI validates against Pydantic schema, rejects extra fields with 422
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_list_workflows(self, client: AsyncClient, sample_workflow_data):
        """Test listing all workflows"""
        # Create workflow
        await client.post("/api/v1/workflows", json=sample_workflow_data)
        
        # List workflows
        response = await client.get("/api/v1/workflows")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == sample_workflow_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_workflow_by_id(self, client: AsyncClient, sample_workflow_data):
        """Test getting workflow by ID"""
        # Create workflow
        create_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["id"]
        
        # Get by ID
        response = await client.get(f"/api/v1/workflows/{workflow_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == workflow_id
        assert data["name"] == sample_workflow_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_workflow(self, client: AsyncClient):
        """Test getting non-existent workflow returns 404"""
        response = await client.get("/api/v1/workflows/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_workflow(self, client: AsyncClient, sample_workflow_data):
        """Test updating workflow"""
        # Create workflow
        create_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["id"]
        
        # Update workflow
        update_data = {
            "name": "Updated Workflow Name",
            "description": "Updated description"
        }
        response = await client.put(f"/api/v1/workflows/{workflow_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
    
    @pytest.mark.asyncio
    async def test_delete_workflow(self, client: AsyncClient, sample_workflow_data):
        """Test deleting workflow"""
        # Create workflow
        create_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["id"]
        
        # Delete workflow
        response = await client.delete(f"/api/v1/workflows/{workflow_id}")
        assert response.status_code == 204
        
        # Verify deleted
        get_response = await client.get(f"/api/v1/workflows/{workflow_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_activate_workflow(self, client: AsyncClient, sample_workflow_data):
        """Test activating workflow"""
        # Create inactive workflow
        sample_workflow_data["is_active"] = False
        create_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["id"]
        
        # Activate
        response = await client.post(f"/api/v1/workflows/{workflow_id}/activate")
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_deactivate_workflow(self, client: AsyncClient, sample_workflow_data):
        """Test deactivating workflow"""
        # Create active workflow
        create_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["id"]
        
        # Deactivate
        response = await client.post(f"/api/v1/workflows/{workflow_id}/deactivate")
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_validate_workflow(self, client: AsyncClient, sample_workflow_data):
        """Test workflow validation"""
        # Create workflow
        create_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = create_response.json()["id"]
        
        # Validate
        response = await client.post(f"/api/v1/workflows/{workflow_id}/validate")
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert "workflow_id" in data
    
    @pytest.mark.asyncio
    async def test_filter_by_persona(self, client: AsyncClient, sample_workflow_data):
        """Test filtering workflows by persona"""
        # Create workflow with STUDENT persona
        await client.post("/api/v1/workflows", json=sample_workflow_data)
        
        # Create workflow with RESEARCHER persona
        researcher_workflow = sample_workflow_data.copy()
        researcher_workflow["name"] = "Researcher Workflow"
        researcher_workflow["persona"] = "researcher"  # Use lowercase to match PersonaEnum
        await client.post("/api/v1/workflows", json=researcher_workflow)
        
        # Filter by student (lowercase)
        response = await client.get("/api/v1/workflows?persona=student")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["persona"] == "student"
    
    @pytest.mark.asyncio
    async def test_search_workflows(self, client: AsyncClient, sample_workflow_data):
        """Test searching workflows"""
        # Create workflow
        await client.post("/api/v1/workflows", json=sample_workflow_data)
        
        # Search
        response = await client.get("/api/v1/workflows?search=Test")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert "Test" in data[0]["name"]
    
    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient, sample_workflow_data):
        """Test workflow pagination"""
        # Create multiple workflows
        for i in range(5):
            workflow_data = sample_workflow_data.copy()
            workflow_data["name"] = f"Workflow {i}"
            await client.post("/api/v1/workflows", json=workflow_data)
        
        # Get first 2
        response = await client.get("/api/v1/workflows?skip=0&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        
        # Get next 2
        response = await client.get("/api/v1/workflows?skip=2&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
