import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

if __name__ == "__main__":
    app_path = BASE_DIR / "dashboard" / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path), "--server.port", "8501"]
    print("=" * 60)
    print("Launching LLM Cost Autopilot Dashboard on http://localhost:8501")
    print("=" * 60)
    subprocess.run(cmd)
