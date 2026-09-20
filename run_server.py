"""Convenience runner script for Brain-Core API Server.

Run easily with:
    python run_server.py
"""
import sys
from pathlib import Path
import uvicorn

# Ensure package root is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

if __name__ == "__main__":
    print("🧠 Starting Brain-Core API Server on http://localhost:8000 ...")
    print("📖 Interactive API Docs available at http://localhost:8000/docs")
    uvicorn.run("brain_core.api.server:app", host="0.0.0.0", port=8000, reload=True)
