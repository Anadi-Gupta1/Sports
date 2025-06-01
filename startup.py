"""
Comprehensive startup script for the Multi-Sport Action Tracker.

This script handles the complete startup process including:
- Environment validation
- Dependency checking
- Database initialization
- Server startup with proper configuration
"""

import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.config.settings import get_settings
from backend.core.tracker import ActionTracker
from backend.feedback.feedback_manager import FeedbackManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/startup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ApplicationStartup:
    """Handles application startup and initialization"""
    
    def __init__(self):
        self.settings = get_settings()
        self.project_root = Path(__file__).parent
        
    async def start_application(self):
        """Start the complete application stack"""
        try:
            print("🚀 Multi-Sport Action Tracker - Starting Application...")
            print("=" * 60)
            
            # Run startup checks
            await self.validate_environment()
            await self.check_dependencies()
            await self.initialize_directories()
            await self.initialize_database()
            await self.test_components()
            
            print("\n✅ All startup checks passed!")
            print("🎯 Starting application servers...\n")
            
            # Start the application
            await self.start_servers()
            
        except Exception as e:
            logger.error(f"Application startup failed: {e}")
            print(f"❌ Startup failed: {e}")
            sys.exit(1)
    
    async def validate_environment(self):
        """Validate environment configuration"""
        print("🔍 Validating environment...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            raise RuntimeError("Python 3.8+ required")
        
        # Check required files
        required_files = [
            ".env",
            "requirements.txt",
            "backend/main.py",
            "frontend/package.json"
        ]
        
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                raise FileNotFoundError(f"Required file missing: {file_path}")
        
        # Check environment variables
        env_file = self.project_root / ".env"
        if env_file.exists():
            logger.info("Environment file found")
        else:
            logger.warning("No .env file found, using defaults")
        
        print("   ✓ Environment validation passed")
    
    async def check_dependencies(self):
        """Check if all dependencies are installed"""
        print("📦 Checking dependencies...")
        
        # Check Python dependencies
        try:
            import fastapi
            import uvicorn
            import opencv_cv2 as cv2
            import mediapipe as mp
            import pygame
            import numpy as np
            print("   ✓ Python dependencies installed")
        except ImportError as e:
            raise RuntimeError(f"Missing Python dependency: {e}")
        
        # Check if Node.js is available
        try:
            result = subprocess.run(
                ["node", "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            print(f"   ✓ Node.js version: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Node.js not found - frontend may not work")
        
        # Check frontend dependencies
        frontend_node_modules = self.project_root / "frontend" / "node_modules"
        if frontend_node_modules.exists():
            print("   ✓ Frontend dependencies installed")
        else:
            print("   ⚠️  Frontend dependencies not found")
            print("   💡 Run: cd frontend && npm install")
    
    async def initialize_directories(self):
        """Initialize required directories"""
        print("📁 Initializing directories...")
        
        directories = [
            "logs",
            "data",
            "models",
            "backend/__pycache__",
            "tests"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
        
        print("   ✓ Directories initialized")
    
    async def initialize_database(self):
        """Initialize database if needed"""
        print("🗄️  Initializing database...")
        
        db_path = self.project_root / "data" / "sessions.db"
        if not db_path.exists():
            # Create empty database file
            db_path.touch()
            logger.info("Database file created")
        
        print("   ✓ Database initialized")
    
    async def test_components(self):
        """Test core components"""
        print("🧪 Testing core components...")
        
        try:
            # Test ActionTracker
            tracker = ActionTracker()
            logger.info("ActionTracker initialized successfully")
            
            # Test FeedbackManager
            feedback_manager = FeedbackManager()
            logger.info("FeedbackManager initialized successfully")
            
            print("   ✓ Core components working")
            
        except Exception as e:
            raise RuntimeError(f"Component test failed: {e}")
    
    async def start_servers(self):
        """Start backend and frontend servers"""
        print("🌐 Starting application servers...")
        
        # Backend server command
        backend_cmd = [
            sys.executable, 
            str(self.project_root / "backend" / "main.py")
        ]
        
        # Frontend server command
        frontend_cmd = ["npm", "start"]
        frontend_cwd = str(self.project_root / "frontend")
        
        print(f"🔧 Backend command: {' '.join(backend_cmd)}")
        print(f"🔧 Frontend command: {' '.join(frontend_cmd)} (in {frontend_cwd})")
        print("\n" + "=" * 60)
        
        try:
            # Start backend server
            print("🚀 Starting backend server...")
            backend_process = subprocess.Popen(
                backend_cmd,
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Wait a moment for backend to start
            await asyncio.sleep(2)
            
            if backend_process.poll() is None:
                print("✅ Backend server started successfully!")
                print("📡 Backend API: http://localhost:8000")
                print("📊 API Docs: http://localhost:8000/docs")
            else:
                print("❌ Backend server failed to start")
                return
            
            # Instructions for frontend
            print("\n🎨 To start the frontend:")
            print("   1. Open a new terminal")
            print("   2. cd frontend")
            print("   3. npm start")
            print("   4. Open http://localhost:3000")
            
            print("\n🎯 Application is ready!")
            print("🛑 Press Ctrl+C to stop the backend server")
            
            # Keep the backend running
            try:
                backend_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping backend server...")
                backend_process.terminate()
                backend_process.wait()
                print("✅ Backend server stopped")
                
        except Exception as e:
            logger.error(f"Failed to start servers: {e}")
            print(f"❌ Server startup failed: {e}")

def print_welcome_message():
    """Print welcome message and instructions"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                  Multi-Sport Action Tracker                 ║
    ║                                                              ║
    ║  🏀 Basketball  🎾 Tennis  ⛳ Golf  ⚽ Soccer                  ║
    ║                                                              ║
    ║  Real-time sports action detection and performance analytics ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

async def main():
    """Main startup function"""
    print_welcome_message()
    
    startup = ApplicationStartup()
    await startup.start_application()

if __name__ == "__main__":
    asyncio.run(main())
