"""
Start the FastAPI development server.
Run this script from the project root directory.
"""
import sys
import os
import uvicorn

# Add src directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, "src")
sys.path.insert(0, src_path)

# Import main app
from main import app
from core.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Server: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"Docs: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("-" * 60)
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        app_dir=src_path
    )
