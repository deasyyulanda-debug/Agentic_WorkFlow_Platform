"""
Pydantic Schemas - Request/Response Models
Type-safe data validation and serialization

Design principles:
- Strict validation (extra='forbid' to prevent typos)
- Clear separation: Request vs Response vs Domain models
- Automatic OpenAPI documentation
- Type hints for IDE support
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict, field_serializer
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums (match database enums)
# ============================================================================

class RunStatusEnum(str, Enum):
    QUEUED = "queued"
    VALIDATING = "validating"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunModeEnum(str, Enum):
    VALIDATE_ONLY = "validate_only"
    TEST_RUN = "test_run"
    FULL_RUN = "full_run"


class ProviderEnum(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"


class PersonaEnum(str, Enum):
    STUDENT = "student"
    RESEARCHER = "researcher"
    ML_ENGINEER = "ml_engineer"
    DATA_SCIENTIST = "data_scientist"
    AI_ARCHITECT = "ai_architect"


# ============================================================================
# Settings Schemas
# ============================================================================

class ProviderInfo(BaseModel):
    """Provider information for listing available providers"""
    name: ProviderEnum
    display_name: str
    description: str
    supported: bool = True
    
    model_config = ConfigDict(from_attributes=True)


class SettingsCreate(BaseModel):
    """Request to create provider settings"""
    provider: ProviderEnum
    api_key: str = Field(..., min_length=10, description="Provider API key")
    is_active: bool = True
    
    model_config = ConfigDict(extra='forbid')


class SettingsUpdate(BaseModel):
    """Request to update provider settings"""
    api_key: Optional[str] = Field(None, min_length=10)
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(extra='forbid')


class SecretCreateRequest(BaseModel):
    """Request to store/update a provider API key"""
    provider: ProviderEnum
    api_key: str = Field(..., min_length=10, description="Provider API key")
    
    model_config = ConfigDict(extra='forbid')


class SecretStatusResponse(BaseModel):
    """Response for secret connection status"""
    provider: ProviderEnum
    connected: bool
    last_tested_at: Optional[datetime] = None
    test_status: Optional[Literal["success", "failed"]] = None
    
    model_config = ConfigDict(from_attributes=True)


class SettingsResponse(BaseModel):
    """Response for getting a setting"""
    id: str
    provider: ProviderEnum
    is_active: bool
    last_tested_at: Optional[datetime] = None
    test_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SettingsTestResponse(BaseModel):
    """Response for testing provider settings"""
    success: bool
    message: str
    provider: str
    tested_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Workflow Schemas
# ============================================================================

class WorkflowCreate(BaseModel):
    """Request to create a workflow"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    persona: PersonaEnum
    definition: Dict[str, Any] = Field(..., description="Workflow step definitions")
    tags: Optional[List[str]] = None
    is_active: bool = True
    
    model_config = ConfigDict(extra='forbid')


class WorkflowUpdate(BaseModel):
    """Request to update a workflow"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(extra='forbid')


class WorkflowSummary(BaseModel):
    """Workflow summary for catalog listing"""
    id: str
    name: str
    description: str
    persona: PersonaEnum
    difficulty_level: Optional[str] = None
    estimated_duration_seconds: Optional[int] = None
    tags: Optional[List[str]] = None
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowSchema(BaseModel):
    """Complete workflow definition including schema"""
    id: str
    name: str
    description: str
    persona: PersonaEnum
    definition: Dict[str, Any]  # Workflow step definitions
    default_config: Optional[Dict[str, Any]] = None
    version: str
    is_active: bool
    estimated_duration_seconds: Optional[int] = None
    difficulty_level: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowResponse(BaseModel):
    """Response for workflow operations"""
    id: str
    name: str
    description: str
    persona: PersonaEnum
    definition: Dict[str, Any] = Field(default_factory=dict)
    tags: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Custom validation to map schema to definition"""
        if hasattr(obj, 'schema'):
            # Create a dict from the object
            data = {
                'id': obj.id,
                'name': obj.name,
                'description': obj.description,
                'persona': obj.persona,
                'definition': obj.schema if obj.schema else {},
                'tags': obj.tags,
                'is_active': obj.is_active,
                'created_at': obj.created_at,
                'updated_at': obj.updated_at
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Run Schemas
# ============================================================================

class RunCreate(BaseModel):
    """Request to create a workflow run"""
    workflow_id: str = Field(..., description="Workflow to execute")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Workflow input parameters")
    mode: RunModeEnum = Field(RunModeEnum.TEST_RUN, description="Execution mode")
    
    @field_validator('input_data')
    @classmethod
    def validate_input_data(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input_data dictionary"""
        if len(v) > 50:
            raise ValueError("Too many input parameters (max 50)")
        return v
    
    model_config = ConfigDict(extra='forbid')


class CreateRunRequest(BaseModel):
    """Request to create and execute a workflow run"""
    workflow_id: str = Field(..., description="Workflow to execute")
    inputs: Dict[str, Any] = Field(..., description="Workflow input parameters")
    run_mode: RunModeEnum = Field(RunModeEnum.TEST_RUN, description="Execution mode")
    provider: ProviderEnum = Field(ProviderEnum.OPENAI, description="LLM provider to use")
    
    @field_validator('inputs')
    @classmethod
    def validate_inputs(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs dictionary"""
        if not v:
            raise ValueError("inputs cannot be empty")
        if len(v) > 50:
            raise ValueError("Too many input fields (max 50)")
        
        # Check for prototype pollution attempts
        forbidden_keys = {'__proto__', 'constructor', 'prototype'}
        if any(key in v for key in forbidden_keys):
            raise ValueError("Forbidden input keys detected")
        
        return v
    
    model_config = ConfigDict(extra='forbid')


class RunResponse(BaseModel):
    """Response for run status and details"""
    id: str
    workflow_id: str
    status: RunStatusEnum
    mode: RunModeEnum  # JSON response uses 'mode'
    input_data: Dict[str, Any]  # JSON response uses 'input_data'
    output_data: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @classmethod
    def model_validate(cls, obj):
        """Custom validation to handle DB field name mapping"""
        if hasattr(obj, 'run_mode'):
            from engine.output_formatter import OutputFormatter
            
            # Map DB field names to response field names
            # Use validation_result as output_data for the frontend
            validation_result = getattr(obj, 'validation_result', None)
            
            # Apply formatting to output_data if it exists and is not already formatted
            formatted_output = validation_result
            if validation_result:
                # Check if this is old format (has 'final' and 'all_steps' but not 'formatted')
                if isinstance(validation_result, dict):
                    # Extract metrics if they exist
                    metrics = validation_result.get('_metrics', {})
                    
                    # Check if it needs formatting (old format)
                    if 'formatted' not in validation_result and ('final' in validation_result or 'all_steps' in validation_result):
                        # Old format - apply formatting
                        output_part = {
                            'final': validation_result.get('final'),
                            'all_steps': validation_result.get('all_steps', [])
                        }
                        formatted_text = OutputFormatter.format_execution_result(output_part, metrics)
                        formatted_output = {
                            'formatted': formatted_text,
                            'raw': output_part
                        }
                        if metrics:
                            formatted_output['_metrics'] = metrics
            
            data = {
                'id': str(obj.id),
                'workflow_id': str(obj.workflow_id),
                'status': obj.status,
                'mode': obj.run_mode,  # DB: run_mode -> JSON: mode
                'input_data': obj.inputs,  # DB: inputs -> JSON: input_data
                'output_data': formatted_output,  # Use validation_result as output_data (with formatting)
                'metrics': getattr(obj, 'metrics', None),
                'validation_result': validation_result,
                'error_message': getattr(obj, 'error_message', None),
                'created_at': obj.created_at,
                'started_at': getattr(obj, 'started_at', None),
                'completed_at': getattr(obj, 'completed_at', None),
            }
            return cls(**data)
        return super().model_validate(obj)
    
    model_config = ConfigDict(from_attributes=True)


class RunListResponse(BaseModel):
    """Response for listing runs (paginated)"""
    runs: List[RunResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class RunExecutionResult(BaseModel):
    """Result of workflow execution with output and metrics"""
    run: RunResponse
    output: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Artifact Schemas
# ============================================================================

class ArtifactCreate(BaseModel):
    """Request to create an artifact"""
    run_id: str
    artifact_type: str
    content: str = Field(..., description="Artifact content")
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra='forbid')


class ArtifactResponse(BaseModel):
    """Response for artifact metadata"""
    id: str
    run_id: str
    artifact_type: str
    file_name: str
    file_path: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ArtifactContentResponse(BaseModel):
    """Response for artifact content"""
    artifact: ArtifactResponse
    content: str  # File content as string
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Validation Schemas
# ============================================================================

class ValidationResult(BaseModel):
    """Result of preflight validation"""
    success: bool
    checks: Dict[str, Any]  # e.g., {"secrets_available": True, "provider_reachable": True}
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    estimated_cost_usd: Optional[str] = None
    
    model_config = ConfigDict(extra='forbid')


# ============================================================================
# Common Responses
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: Literal["healthy", "unhealthy"]
    version: str
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    
    model_config = ConfigDict(extra='forbid')


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    message: str
    
    model_config = ConfigDict(extra='forbid')
