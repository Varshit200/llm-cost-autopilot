import os
import sys
import zipfile
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Target export destinations
DOWNLOADS_DIR = Path("C:/Users/varsh/Downloads")
DESKTOP_DIR = Path("C:/Users/varsh/Desktop")

EXCLUDE_DIRS = {".venv", "__pycache__", ".git", ".pytest_cache", ".idea", ".vscode"}
EXCLUDE_EXTS = {".pyc", ".pyo"}

def create_project_zip(output_zip_path: Path):
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Modify dirs in-place to avoid traversing excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in EXCLUDE_EXTS or file.endswith(".zip"):
                    continue
                
                # Relative path inside the zip archive
                rel_path = file_path.relative_to(BASE_DIR)
                zipf.write(file_path, arcname=str(Path("llm-cost-autopilot") / rel_path))
    
    file_size_mb = output_zip_path.stat().st_size / (1024 * 1024)
    print(f"Created ZIP: {output_zip_path} ({file_size_mb:.2f} MB)")

def copy_unzipped_folder(target_dir: Path):
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
    
    shutil.copytree(
        BASE_DIR,
        target_dir,
        ignore=shutil.ignore_patterns(".venv", "__pycache__", "*.pyc", "*.zip")
    )
    print(f"Copied unzipped project to: {target_dir}")

if __name__ == "__main__":
    print("=" * 60)
    print("Packaging LLM Cost Autopilot for user download...")
    print("=" * 60)

    # 1. Create ZIP in project folder
    local_zip = BASE_DIR / "llm-cost-autopilot.zip"
    create_project_zip(local_zip)

    # 2. Copy ZIP to Downloads
    if DOWNLOADS_DIR.exists():
        downloads_zip = DOWNLOADS_DIR / "llm-cost-autopilot.zip"
        shutil.copy2(local_zip, downloads_zip)
        print(f"Delivered to Downloads: {downloads_zip}")
        
        # Also copy ready-to-run unzipped folder to Downloads
        unzipped_downloads = DOWNLOADS_DIR / "llm-cost-autopilot"
        copy_unzipped_folder(unzipped_downloads)

    # 3. Copy ZIP to Desktop for instant access
    if DESKTOP_DIR.exists():
        desktop_zip = DESKTOP_DIR / "llm-cost-autopilot.zip"
        shutil.copy2(local_zip, desktop_zip)
        print(f"Delivered to Desktop: {desktop_zip}")

    print("=" * 60)
    print("Project successfully packaged and placed in user directories!")
