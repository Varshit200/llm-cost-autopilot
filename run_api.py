import sys
from pathlib import Path
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    print("=" * 60)
    print("Starting LLM Cost Autopilot API on http://127.0.0.1:8000")
    print("Docs available at: http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=False)
