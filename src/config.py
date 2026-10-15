import os
from pathlib import Path
from typing import Dict, Any
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

class Settings:
    PROJECT_NAME: str = "LLM Cost Autopilot"
    VERSION: str = "1.0.0"
    
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    MODELS_DIR: Path = MODELS_DIR
    
    # Environment configs
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_PROVIDER_MODE: str = os.getenv("LLM_PROVIDER_MODE", "auto").lower()
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'autopilot.db'}")
    SQLITE_PATH: Path = DATA_DIR / "autopilot.db"
    
    CLASSIFIER_MODEL_PATH: Path = MODELS_DIR / "classifier.pkl"
    DATASET_TRAIN_PATH: Path = DATA_DIR / "dataset_train.json"

    @staticmethod
    def load_yaml(file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @classmethod
    def get_models_config(cls) -> Dict[str, Any]:
        return cls.load_yaml(CONFIG_DIR / "models.yaml").get("models", {})

    @classmethod
    def get_routing_config(cls) -> Dict[str, Any]:
        return cls.load_yaml(CONFIG_DIR / "routing_config.yaml")

    @classmethod
    def save_routing_config(cls, new_config: Dict[str, Any]) -> None:
        target = CONFIG_DIR / "routing_config.yaml"
        with open(target, "w", encoding="utf-8") as f:
            yaml.safe_dump(new_config, f, sort_keys=False, indent=2)

settings = Settings()
