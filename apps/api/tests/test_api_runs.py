"""
Runs API Endpoint Tests
Tests for workflow run operations
"""
import pytest
from httpx import AsyncClient


class TestRunsAPI:
    """Test Runs API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_run(
        self, 
        client: AsyncClient, 
        sample_workflow_data, 
        sample_run_data
    ):
        """Test creating a run"""
        # Create workflow first
        workflow_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = workflow_response.json()["id"]
        
        # Create run
        run_data = sample_run_data.copy()
        run_data["workflow_id"] = workflow_id
        
        response = await client.post("/api/v1/runs", json=run_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["workflow_id"] == workflow_id
        assert data["status"] == "queued"  # Lowercase to match RunStatus enum
        assert data["mode"] == run_data["mode"]  # Changed from run_mode to mode
        assert "id" in data
        assert "created_at" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_run_nonexistent_workflow(
        self, 
        client: AsyncClient, 
        sample_run_data
    ):
        """Test creating run with non-existent workflow"""
        run_data = sample_run_data.copy()
        run_data["workflow_id"] = "00000000-0000-0000-0000-000000000000"
        
        response = await client.post("/api/v1/runs", json=run_data)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_runs(
        self, 
        client: AsyncClient, 
        sample_workflow_data, 
        sample_run_data
    ):
        """Test listing all runs"""
        # Create workflow
        workflow_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = workflow_response.json()["id"]
        
        # Create run
        run_data = sample_run_data.copy()
        run_data["workflow_id"] = workflow_id
        await client.post("/api/v1/runs", json=run_data)
        
        # List runs
        response = await client.get("/api/v1/runs")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["workflow_id"] == workflow_id
    
    @pytest.mark.asyncio
    async def test_get_run_by_id(
        self, 
        client: AsyncClient, 
        sample_workflow_data, 
        sample_run_data
    ):
        """Test getting run by ID"""
        # Create workflow
        workflow_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = workflow_response.json()["id"]
        
        # Create run
        run_data = sample_run_data.copy()
        run_data["workflow_id"] = workflow_id
        create_response = await client.post("/api/v1/runs", json=run_data)
        run_id = create_response.json()["id"]
        
        # Get by ID
        response = await client.get(f"/api/v1/runs/{run_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == run_id
        assert data["workflow_id"] == workflow_id
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_run(self, client: AsyncClient):
        """Test getting non-existent run returns 404"""
        response = await client.get("/api/v1/runs/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_run(
        self, 
        client: AsyncClient, 
        sample_workflow_data, 
        sample_run_data
    ):
        """Test deleting run"""
        # Create workflow
        workflow_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = workflow_response.json()["id"]
        
        # Create run
        run_data = sample_run_data.copy()
        run_data["workflow_id"] = workflow_id
        create_response = await client.post("/api/v1/runs", json=run_data)
        run_id = create_response.json()["id"]
        
        # Delete run
        response = await client.delete(f"/api/v1/runs/{run_id}")
        assert response.status_code == 204
        
        # Verify deleted
        get_response = await client.get(f"/api/v1/runs/{run_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_run_status(
        self, 
        client: AsyncClient, 
        sample_workflow_data, 
        sample_run_data
    ):
        """Test getting run status"""
        # Create workflow
        workflow_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = workflow_response.json()["id"]
        
        # Create run
        run_data = sample_run_data.copy()
        run_data["workflow_id"] = workflow_id
        create_response = await client.post("/api/v1/runs", json=run_data)
        run_id = create_response.json()["id"]
        
        # Get status
        response = await client.get(f"/api/v1/runs/{run_id}/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["run_id"] == run_id
        assert data["status"] == "queued"  # Lowercase to match RunStatus enum
        assert "started_at" in data
        assert "completed_at" in data
    
    @pytest.mark.asyncio
    async def test_filter_by_workflow_id(
        self, 
        client: AsyncClient, 
        sample_workflow_data, 
        sample_run_data
    ):
        """Test filtering runs by workflow ID"""
        # Create two workflows
        workflow1_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow1_id = workflow1_response.json()["id"]
        
        workflow2_data = sample_workflow_data.copy()
        workflow2_data["name"] = "Workflow 2"
        workflow2_response = await client.post("/api/v1/workflows", json=workflow2_data)
        workflow2_id = workflow2_response.json()["id"]
        
        # Create runs for both workflows
        run_data1 = sample_run_data.copy()
        run_data1["workflow_id"] = workflow1_id
        await client.post("/api/v1/runs", json=run_data1)
        
        run_data2 = sample_run_data.copy()
        run_data2["workflow_id"] = workflow2_id
        await client.post("/api/v1/runs", json=run_data2)
        
        # Filter by workflow1
        response = await client.get(f"/api/v1/runs?workflow_id={workflow1_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["workflow_id"] == workflow1_id
    
    @pytest.mark.asyncio
    async def test_filter_by_status(
        self, 
        client: AsyncClient, 
        sample_workflow_data, 
        sample_run_data
    ):
        """Test filtering runs by status"""
        # Create workflow
        workflow_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = workflow_response.json()["id"]
        
        # Create run
        run_data = sample_run_data.copy()
        run_data["workflow_id"] = workflow_id
        await client.post("/api/v1/runs", json=run_data)
        
        # Filter by queued status (lowercase to match RunStatusEnum)
        response = await client.get("/api/v1/runs?status_filter=queued")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "queued"  # Lowercase to match RunStatus enum value
    
    @pytest.mark.asyncio
    async def test_pagination(
        self, 
        client: AsyncClient, 
        sample_workflow_data, 
        sample_run_data
    ):
        """Test run pagination"""
        # Create workflow
        workflow_response = await client.post("/api/v1/workflows", json=sample_workflow_data)
        workflow_id = workflow_response.json()["id"]
        
        # Create multiple runs
        for i in range(5):
            run_data = sample_run_data.copy()
            run_data["workflow_id"] = workflow_id
            await client.post("/api/v1/runs", json=run_data)
        
        # Get first 2
        response = await client.get("/api/v1/runs?skip=0&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
