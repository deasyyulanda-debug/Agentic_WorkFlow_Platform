"""
Workflow Service - Workflow Management
Handles CRUD operations for workflows
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Workflow as WorkflowModel, Persona
from db.repositories import WorkflowRepository
from models.schemas import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse
)
from core import (
    WorkflowNotFoundError,
    InvalidWorkflowError,
    get_logger
)


class WorkflowService:
    """
    Service for managing workflows.
    
    Responsibilities:
    - Workflow CRUD operations
    - Workflow validation
    - Persona filtering
    - Tag-based search
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = WorkflowRepository(session)
        self.logger = get_logger(__name__)
    
    async def create_workflow(self, data: WorkflowCreate) -> WorkflowResponse:
        """
        Create a new workflow.
        
        Args:
            data: Workflow creation data
            
        Returns:
            Created workflow
            
        Raises:
            InvalidWorkflowError: If workflow definition is invalid
        """
        # Validate workflow structure
        self._validate_workflow_definition(data.definition)
        
        self.logger.info(f"Creating workflow: {data.name}")
        
        # Generate workflow ID
        import uuid
        workflow_id = str(uuid.uuid4())
        
        # Create workflow
        workflow = await self.repository.create(
            id=workflow_id,
            name=data.name,
            description=data.description,
            persona=data.persona,
            schema=data.definition,  # DB model uses 'schema' field
            tags=data.tags,
            is_active=data.is_active
        )
        
        self.logger.info(f"Workflow created: {workflow.id}")
        
        return WorkflowResponse.model_validate(workflow)
    
    async def get_workflow(self, workflow_id: str) -> WorkflowResponse:
        """Get workflow by ID"""
        workflow = await self.repository.get(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(workflow_id)
        
        return WorkflowResponse.model_validate(workflow)
    
    async def list_workflows(
        self,
        persona: Optional[Persona] = None,
        active_only: bool = False,
        tag: Optional[str] = None
    ) -> list[WorkflowResponse]:
        """
        List workflows with optional filters.
        
        Args:
            persona: Filter by persona
            active_only: Return only active workflows
            tag: Filter by tag
            
        Returns:
            List of workflows
        """
        if persona:
            workflows = await self.repository.get_by_persona(persona)
        elif tag:
            workflows = await self.repository.search_by_tag(tag)
        elif active_only:
            workflows = await self.repository.get_active()
        else:
            workflows = await self.repository.list()
        
        return [WorkflowResponse.model_validate(w) for w in workflows]
    
    async def update_workflow(
        self,
        workflow_id: str,
        data: WorkflowUpdate
    ) -> WorkflowResponse:
        """
        Update a workflow.
        
        Args:
            workflow_id: Workflow ID
            data: Update data
            
        Returns:
            Updated workflow
        """
        workflow = await self.repository.get(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(workflow_id)
        
        update_dict = data.model_dump(exclude_unset=True)
        
        # Validate definition if it's being updated
        if "definition" in update_dict:
            self._validate_workflow_definition(update_dict["definition"])
        
        # Update workflow
        updated = await self.repository.update(workflow_id, **update_dict)
        
        self.logger.info(f"Workflow updated: {workflow_id}")
        
        return WorkflowResponse.model_validate(updated)
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if deleted
        """
        workflow = await self.repository.get(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(workflow_id)
        
        await self.repository.delete(workflow_id)
        
        self.logger.info(f"Workflow deleted: {workflow_id}")
        
        return True
    
    async def activate_workflow(self, workflow_id: str) -> WorkflowResponse:
        """Activate a workflow"""
        workflow = await self.repository.get(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(workflow_id)
        
        updated = await self.repository.update(workflow_id, is_active=True)
        self.logger.info(f"Workflow activated: {workflow_id}")
        
        return WorkflowResponse.model_validate(updated)
    
    async def deactivate_workflow(self, workflow_id: str) -> WorkflowResponse:
        """Deactivate a workflow"""
        workflow = await self.repository.get(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(workflow_id)
        
        updated = await self.repository.update(workflow_id, is_active=False)
        self.logger.info(f"Workflow deactivated: {workflow_id}")
        
        return WorkflowResponse.model_validate(updated)
    
    def _validate_workflow_definition(self, definition: dict) -> None:
        """
        Validate workflow definition structure.
        
        Args:
            definition: Workflow definition to validate
            
        Raises:
            InvalidWorkflowError: If definition is invalid
        """
        # Basic validation - workflow must have required fields
        required_fields = ["steps"]
        
        for field in required_fields:
            if field not in definition:
                raise InvalidWorkflowError(
                    f"Missing required field: {field}"
                )
        
        # Validate steps
        steps = definition.get("steps", [])
        if not isinstance(steps, list):
            raise InvalidWorkflowError("'steps' must be a list")
        
        if len(steps) == 0:
            raise InvalidWorkflowError("Workflow must have at least one step")
        
        # Validate each step
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise InvalidWorkflowError(f"Step {i} must be a dictionary")
            
            # Each step should have a type
            if "type" not in step:
                raise InvalidWorkflowError(f"Step {i} missing 'type' field")
            
            # Validate step type
            valid_types = ["prompt", "transform", "validate", "branch", "rag_ingest", "rag_retrieve"]
            if step["type"] not in valid_types:
                raise InvalidWorkflowError(
                    f"Step {i} has invalid type: {step['type']}. "
                    f"Valid types: {', '.join(valid_types)}"
                )
        
        self.logger.debug(f"Workflow definition validated: {len(steps)} steps")
