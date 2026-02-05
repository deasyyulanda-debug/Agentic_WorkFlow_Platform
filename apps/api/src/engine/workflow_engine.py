"""
Workflow Engine - Core execution engine for workflows
Orchestrates workflow execution with different run modes
"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import RunMode, RunStatus
from services import (
    SettingsService,
    WorkflowService,
    RunService,
    ArtifactService
)
from providers import get_provider, LLMRequest
from core import (
    get_logger,
    WorkflowExecutionError,
    MaxIterationsExceededError,
    TokenLimitExceededError,
    TimeoutExceededError,
    settings
)
from .output_formatter import OutputFormatter


class WorkflowEngine:
    """
    Core workflow execution engine.
    
    Responsibilities:
    - Execute workflow steps sequentially
    - Enforce run mode limits (TestRun, FullRun)
    - Track metrics (tokens, time, iterations)
    - Store artifacts (prompts, responses)
    - Handle errors gracefully
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings_service = SettingsService(session)
        self.workflow_service = WorkflowService(session)
        self.run_service = RunService(session)
        self.artifact_service = ArtifactService(session)
        self.logger = get_logger(__name__)
    
    async def execute(self, run_id: str) -> Dict[str, Any]:
        """
        Execute a workflow run.
        
        Args:
            run_id: Run ID to execute
            
        Returns:
            Execution result with output and metrics
            
        Raises:
            WorkflowExecutionError: If execution fails
            MaxIterationsExceededError: If max iterations exceeded (test mode)
            TokenLimitExceededError: If token limit exceeded (test mode)
            TimeoutExceededError: If timeout exceeded (test mode)
        """
        # Get run and workflow
        run = await self.run_service.get_run(run_id)
        workflow = await self.workflow_service.get_workflow(run.workflow_id)
        
        self.logger.info(
            f"Starting execution: run={run_id}, workflow={workflow.name}, mode={run.mode.value}",
            run_id=run_id
        )
        
        try:
            # Start the run
            await self.run_service.start_run(run_id)
            
            # Execute based on mode
            if run.mode == RunMode.VALIDATE_ONLY:
                result = await self._execute_validate_only(run_id, workflow, run)
            elif run.mode == RunMode.TEST_RUN:
                result = await self._execute_test_run(run_id, workflow, run)
            else:  # FULL_RUN
                result = await self._execute_full_run(run_id, workflow, run)
            
            # Complete the run
            await self.run_service.complete_run(
                run_id,
                output_data=result["output"],
                metrics=result["metrics"]
            )
            
            self.logger.info(
                f"Execution completed: run={run_id}",
                run_id=run_id,
                metrics=result["metrics"]
            )
            
            return result
            
        except (
            MaxIterationsExceededError,
            TokenLimitExceededError,
            TimeoutExceededError
        ) as e:
            # Limit exceeded - fail the run
            await self.run_service.fail_run(
                run_id,
                error_message=e.message,
                error_details=e.details
            )
            raise
            
        except Exception as e:
            # Unexpected error - fail the run
            error_msg = str(e)
            self.logger.exception(f"Execution failed: run={run_id}", run_id=run_id)
            
            await self.run_service.fail_run(
                run_id,
                error_message=error_msg,
                error_details={"type": type(e).__name__}
            )
            raise WorkflowExecutionError(error_msg, run_id)
    
    async def _execute_validate_only(
        self,
        run_id: str,
        workflow: Any,
        run: Any
    ) -> Dict[str, Any]:
        """
        Execute workflow in validate-only mode.
        Only validates workflow structure, no LLM calls.
        """
        self.logger.info(f"Validating workflow: {workflow.name}", run_id=run_id)
        
        validation_errors = []
        
        # Validate workflow definition
        definition = workflow.definition
        steps = definition.get("steps", [])
        
        for i, step in enumerate(steps):
            step_type = step.get("type")
            
            # Validate step has required fields
            if step_type == "prompt":
                if "template" not in step:
                    validation_errors.append(f"Step {i}: Missing 'template' field")
            elif step_type == "transform":
                if "function" not in step:
                    validation_errors.append(f"Step {i}: Missing 'function' field")
            elif step_type == "validate":
                if "rules" not in step:
                    validation_errors.append(f"Step {i}: Missing 'rules' field")
        
        # Store validation result
        from models.schemas import ValidationResult
        result = ValidationResult(
            is_valid=len(validation_errors) == 0,
            errors=validation_errors,
            warnings=[]
        )
        
        await self.run_service.update_validation_result(run_id, result)
        
        return {
            "output": {"validation": result.model_dump()},
            "metrics": {
                "steps_validated": len(steps),
                "errors_found": len(validation_errors)
            }
        }
    
    async def _execute_test_run(
        self,
        run_id: str,
        workflow: Any,
        run: Any
    ) -> Dict[str, Any]:
        """
        Execute workflow in test-run mode.
        Enforces limits: max tokens, max runtime, max iterations.
        """
        self.logger.info(f"Test run execution: {workflow.name}", run_id=run_id)
        
        # Get limits from settings
        max_tokens = settings.TEST_RUN_MAX_TOKENS
        max_runtime = settings.TEST_RUN_MAX_RUNTIME_SECONDS
        max_iterations = settings.TEST_RUN_MAX_ITERATIONS
        
        start_time = datetime.utcnow()
        
        # Execute with limits
        result = await self._execute_steps(
            run_id,
            workflow,
            run,
            max_tokens=max_tokens,
            max_runtime=max_runtime,
            max_iterations=max_iterations,
            start_time=start_time
        )
        
        return result
    
    async def _execute_full_run(
        self,
        run_id: str,
        workflow: Any,
        run: Any
    ) -> Dict[str, Any]:
        """
        Execute workflow in full-run mode.
        No limits enforced.
        """
        self.logger.info(f"Full run execution: {workflow.name}", run_id=run_id)
        
        start_time = datetime.utcnow()
        
        # Execute without limits
        result = await self._execute_steps(
            run_id,
            workflow,
            run,
            start_time=start_time
        )
        
        return result
    
    async def _execute_steps(
        self,
        run_id: str,
        workflow: Any,
        run: Any,
        max_tokens: Optional[int] = None,
        max_runtime: Optional[int] = None,
        max_iterations: Optional[int] = None,
        start_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Execute workflow steps sequentially.
        
        Args:
            run_id: Run ID
            workflow: Workflow definition
            run: Run instance
            max_tokens: Maximum tokens allowed (test mode)
            max_runtime: Maximum runtime in seconds (test mode)
            max_iterations: Maximum iterations allowed (test mode)
            start_time: Execution start time
            
        Returns:
            Execution result
        """
        definition = workflow.definition
        steps = definition.get("steps", [])
        
        # Initialize execution context
        context = {
            "input": run.input_data,
            "variables": {},
            "outputs": []
        }
        
        # Initialize metrics
        total_tokens = 0
        iteration_count = 0
        
        # Get provider settings (assuming first active settings)
        all_settings = await self.settings_service.list_settings(active_only=True, tested_only=False)
        if not all_settings:
            raise WorkflowExecutionError("No active provider settings found", run_id)
        
        provider_settings = all_settings[0]  # Use first available
        
        # Get decrypted API key
        api_key = await self.settings_service.get_decrypted_api_key(provider_settings.id)
        
        # Create provider
        provider = get_provider(
            provider_settings.provider.value,
            api_key
        )
        
        self.logger.info(
            f"Using provider: {provider_settings.provider.value}",
            run_id=run_id
        )
        
        # Execute each step
        for step_index, step in enumerate(steps):
            iteration_count += 1
            
            # Check limits (test mode)
            if max_iterations and iteration_count > max_iterations:
                raise MaxIterationsExceededError(max_iterations, run_id)
            
            if max_runtime and start_time:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed > max_runtime:
                    raise TimeoutExceededError(max_runtime, run_id)
            
            if max_tokens and total_tokens > max_tokens:
                raise TokenLimitExceededError(max_tokens, run_id)
            
            # Execute step
            # Use model from step config, or default based on provider
            model = step.get("model", "gemini-2.0-flash" if provider_settings.provider.value == "gemini" else "gpt-4")
            step_result = await self._execute_step(
                run_id,
                step,
                step_index,
                context,
                provider,
                model
            )
            
            # Track tokens
            tokens_used = step_result.get("tokens", 0)
            total_tokens += tokens_used
            
            # Store output
            context["outputs"].append(step_result)
            
            self.logger.info(
                f"Step {step_index} completed: {step.get('type')}",
                run_id=run_id,
                tokens=tokens_used
            )
        
        # Calculate final metrics
        if start_time:
            duration = (datetime.utcnow() - start_time).total_seconds()
        else:
            duration = 0
        
        metrics = {
            "total_tokens": total_tokens,
            "duration_seconds": duration,
            "steps_executed": len(steps),
            "iterations": iteration_count,
            "provider": provider_settings.provider.value
        }
        
        output_data = {
            "final": context["outputs"][-1] if context["outputs"] else None,
            "all_steps": context["outputs"]
        }
        
        # Format the output in a readable format
        formatted_output = OutputFormatter.format_execution_result(output_data, metrics)
        
        return {
            "output": {
                "formatted": formatted_output,
                "raw": output_data  # Keep raw data for programmatic access
            },
            "metrics": metrics
        }
    
    async def _execute_step(
        self,
        run_id: str,
        step: Dict[str, Any],
        step_index: int,
        context: Dict[str, Any],
        provider: Any,
        model: str
    ) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step_type = step.get("type")
        
        if step_type == "prompt":
            return await self._execute_prompt_step(
                run_id,
                step,
                step_index,
                context,
                provider,
                model
            )
        elif step_type == "transform":
            return await self._execute_transform_step(step, context)
        elif step_type == "validate":
            return await self._execute_validate_step(step, context)
        else:
            raise WorkflowExecutionError(f"Unknown step type: {step_type}", run_id)
    
    async def _execute_prompt_step(
        self,
        run_id: str,
        step: Dict[str, Any],
        step_index: int,
        context: Dict[str, Any],
        provider: Any,
        model: str
    ) -> Dict[str, Any]:
        """Execute a prompt step (LLM call)"""
        # Build prompt from template
        template = step.get("template", "")
        prompt = self._render_template(template, context)
        
        # Get system prompt if specified
        system_prompt = step.get("system_prompt")
        if system_prompt:
            system_prompt = self._render_template(system_prompt, context)
        
        # Store prompt artifact
        import json
        from models.schemas import ArtifactCreate
        await self.artifact_service.create_artifact(
            ArtifactCreate(
                run_id=run_id,
                artifact_type="prompt",
                content=json.dumps({"prompt": prompt, "system": system_prompt, "step": step_index}),
                metadata={"step_index": step_index}
            )
        )
        
        # Create LLM request
        request = LLMRequest(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            temperature=step.get("temperature", 0.7),
            max_tokens=step.get("max_tokens")
        )
        
        # Call provider
        response = await provider.generate(request)
        
        # Store response artifact
        await self.artifact_service.create_artifact(
            ArtifactCreate(
                run_id=run_id,
                artifact_type="response",
                content=json.dumps(response.to_dict()),
                metadata={"step_index": step_index}
            )
        )
        
        # Update context
        output_var = step.get("output_variable", f"step_{step_index}_output")
        context["variables"][output_var] = response.content
        
        return {
            "type": "prompt",
            "output": response.content,
            "tokens": response.usage.get("total_tokens", 0),
            "variable": output_var
        }
    
    async def _execute_transform_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a transform step (data manipulation)"""
        # Simple transformation: extract variable
        function = step.get("function")
        
        if function == "extract":
            # Extract value from previous output
            source = step.get("source", "")
            value = context["variables"].get(source, "")
            
            output_var = step.get("output_variable", "transformed")
            context["variables"][output_var] = value
            
            return {
                "type": "transform",
                "output": value,
                "tokens": 0,
                "variable": output_var
            }
        else:
            return {
                "type": "transform",
                "output": None,
                "tokens": 0
            }
    
    async def _execute_validate_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a validation step"""
        rules = step.get("rules", [])
        source_var = step.get("source")
        value = context["variables"].get(source_var, "")
        
        validation_passed = True
        errors = []
        
        for rule in rules:
            rule_type = rule.get("type")
            
            if rule_type == "not_empty":
                if not value or not value.strip():
                    validation_passed = False
                    errors.append("Value is empty")
            elif rule_type == "min_length":
                min_len = rule.get("value", 0)
                if len(value) < min_len:
                    validation_passed = False
                    errors.append(f"Value too short (min: {min_len})")
        
        return {
            "type": "validate",
            "output": {"valid": validation_passed, "errors": errors},
            "tokens": 0
        }
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render template with context variables.
        Simple variable substitution: {{variable_name}}
        """
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            # Try variables first, then input
            if var_name in context["variables"]:
                return str(context["variables"][var_name])
            elif var_name in context.get("input", {}):
                return str(context["input"][var_name])
            else:
                return match.group(0)  # Keep original if not found
        
        # Replace {{variable}} patterns
        rendered = re.sub(r'\{\{([^}]+)\}\}', replace_var, template)
        
        return rendered
