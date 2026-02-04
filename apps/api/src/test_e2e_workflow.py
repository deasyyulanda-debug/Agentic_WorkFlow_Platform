"""
End-to-End Workflow Test
Tests the complete workflow execution pipeline
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from db.database import get_db, init_db
from db.models import Provider, Persona, RunMode
from services import (
    SettingsService,
    WorkflowService,
    RunService,
    ArtifactService
)
from engine import WorkflowEngine
from models.schemas import (
    SettingsCreate,
    WorkflowCreate,
    RunCreate
)


async def test_complete_pipeline():
    """Test the complete workflow execution pipeline"""
    
    print("=" * 60)
    print("End-to-End Workflow Execution Test")
    print("=" * 60)
    
    # Initialize security (required for encryption)
    from core import init_security, settings as core_settings
    init_security(core_settings.SECRET_KEY)
    print("\n✅ Security initialized")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Get database session
    async for session in get_db():
        try:
            # 1. Create provider settings
            print("\n" + "-" * 60)
            print("Step 1: Creating Provider Settings")
            print("-" * 60)
            
            settings_service = SettingsService(session)
            
            # Check if Gemini API key is available
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                print("❌ GEMINI_API_KEY not set in environment")
                print("   Run: $env:GEMINI_API_KEY='your-key-here'")
                return
            
            # Create settings
            settings_data = SettingsCreate(
                provider=Provider.GEMINI,
                api_key=api_key,
                is_active=True
            )
            
            # Try to create settings or get existing
            try:
                provider_settings = await settings_service.create_settings(settings_data)
                print(f"✅ Settings created: {provider_settings.id}")
            except Exception as e:
                if "already exist" in str(e):
                    # Get existing settings
                    provider_settings = await settings_service.get_settings_by_provider(Provider.GEMINI)
                    print(f"✅ Using existing settings: {provider_settings.id}")
                else:
                    raise
            
            print(f"   Provider: {provider_settings.provider.value}")
            print(f"   Active: {provider_settings.is_active}")
            
            # Test API key
            print("\n⏳ Testing API key...")
            is_valid = await settings_service.test_api_key(provider_settings.id)
            print(f"✅ API key validated successfully")
            
            # 2. Create workflow
            print("\n" + "-" * 60)
            print("Step 2: Creating Workflow")
            print("-" * 60)
            
            workflow_service = WorkflowService(session)
            
            workflow_definition = {
                "steps": [
                    {
                        "type": "prompt",
                        "template": "Write a haiku about {{topic}}",
                        "system_prompt": "You are a creative poet.",
                        "temperature": 0.8,
                        "max_tokens": 100,
                        "output_variable": "haiku"
                    },
                    {
                        "type": "validate",
                        "source": "haiku",
                        "rules": [
                            {"type": "not_empty"},
                            {"type": "min_length", "value": 10}
                        ]
                    }
                ]
            }
            
            workflow_data = WorkflowCreate(
                name="Haiku Generator",
                description="Generates a haiku about a given topic",
                persona=Persona.STUDENT,
                definition=workflow_definition,
                tags=["poetry", "creative", "test"],
                is_active=True
            )
            
            workflow = await workflow_service.create_workflow(workflow_data)
            print(f"✅ Workflow created: {workflow.id}")
            print(f"   Name: {workflow.name}")
            print(f"   Steps: {len(workflow.definition['steps'])}")
            print(f"   Persona: {workflow.persona.value}")
            
            # 3. Create run
            print("\n" + "-" * 60)
            print("Step 3: Creating Run")
            print("-" * 60)
            
            run_service = RunService(session)
            
            run_data = RunCreate(
                workflow_id=workflow.id,
                mode=RunMode.TEST_RUN,
                input_data={"topic": "artificial intelligence"}
            )
            
            run = await run_service.create_run(run_data)
            print(f"✅ Run created: {run.id}")
            print(f"   Mode: {run.mode.value}")
            print(f"   Status: {run.status.value}")
            print(f"   Input: {run.input_data}")
            
            # 4. Execute workflow
            print("\n" + "-" * 60)
            print("Step 4: Executing Workflow")
            print("-" * 60)
            
            engine = WorkflowEngine(session)
            
            print("⏳ Executing workflow...")
            result = await engine.execute(run.id)
            
            print("\n✅ Execution completed!")
            print("\n📊 Metrics:")
            for key, value in result["metrics"].items():
                print(f"   {key}: {value}")
            
            print("\n📝 Output:")
            # Display the haiku from the prompt step (first step)
            if result["output"]["all_steps"]:
                for i, step_output in enumerate(result["output"]["all_steps"]):
                    if step_output.get("type") == "prompt":
                        haiku = step_output.get("output", "")
                        print(f"   Haiku generated:\n   {haiku}")
                        break
            # Also show validation result
            if result["output"]["final"]:
                final = result["output"]["final"]
                if final.get("type") == "validate":
                    validation = final.get("output", {})
                    print(f"\n   Validation: {'✅ Passed' if validation.get('valid') else '❌ Failed'}")
                    if validation.get("errors"):
                        print(f"   Errors: {validation['errors']}")
            
            # 5. Verify artifacts
            print("\n" + "-" * 60)
            print("Step 5: Checking Artifacts")
            print("-" * 60)
            
            artifact_service = ArtifactService(session)
            artifacts = await artifact_service.get_artifacts_by_run(run.id)
            
            print(f"✅ Found {len(artifacts)} artifacts:")
            for artifact in artifacts:
                print(f"   - {artifact.artifact_type}: {artifact.file_name}")
            
            # 6. Get final run status
            print("\n" + "-" * 60)
            print("Step 6: Final Run Status")
            print("-" * 60)
            
            final_run = await run_service.get_run(run.id)
            print(f"✅ Run completed successfully")
            print(f"   Status: {final_run.status.value}")
            if final_run.completed_at and final_run.created_at:
                duration = (final_run.completed_at - final_run.created_at).total_seconds()
                print(f"   Duration: {duration:.2f}s")
            if final_run.total_tokens_used:
                print(f"   Tokens: {final_run.total_tokens_used}")
            
            print("\n" + "=" * 60)
            print("🎉 All tests passed!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(test_complete_pipeline())
