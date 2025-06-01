#!/usr/bin/env python3
"""
Simple server startup script for the Multi-Sport Action Tracker
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# Now import and run the main application
if __name__ == "__main__":
    os.chdir(project_root / "backend")
    
    # Import uvicorn and run the server
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(project_root / "backend")]
    )
