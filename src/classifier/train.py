import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from src.config import settings
from src.classifier.features import extract_features, features_to_vector, FEATURE_NAMES

logger = logging.getLogger("autopilot.classifier.train")

def load_dataset(dataset_path: Path) -> Tuple[np.ndarray, np.ndarray, list]:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    X_list = []
    y_list = []
    prompts = []

    for item in data:
        prompt = item["prompt"]
        tier = item["tier"]
        feats = item.get("features") or extract_features(prompt)
        vec = features_to_vector(feats)
        
        X_list.append(vec)
        y_list.append(tier)
        prompts.append(prompt)

    return np.array(X_list), np.array(y_list), prompts

def train_and_save_classifier(dataset_path: Path = None, output_path: Path = None) -> Dict[str, Any]:
    dataset_path = dataset_path or settings.DATASET_TRAIN_PATH
    output_path = output_path or settings.CLASSIFIER_MODEL_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)

    X, y, prompts = load_dataset(dataset_path)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Random Forest with calibrated probabilities
    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=10,
        random_state=42,
        class_weight="balanced"
    )
    clf.fit(X_train_scaled, y_train)

    y_pred = clf.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred, labels=["tier_1", "tier_2", "tier_3"]).tolist()

    # Feature importances
    importances = {name: float(imp) for name, imp in zip(FEATURE_NAMES, clf.feature_importances_)}

    package = {
        "model": clf,
        "scaler": scaler,
        "feature_names": FEATURE_NAMES,
        "classes": clf.classes_.tolist(),
        "accuracy": float(acc),
        "classification_report": report,
        "confusion_matrix": cm,
        "feature_importances": importances
    }

    joblib.dump(package, output_path)

    return {
        "accuracy": acc,
        "sample_count": len(X),
        "test_count": len(X_test),
        "confusion_matrix": cm,
        "classification_report": report,
        "model_path": str(output_path),
        "feature_importances": importances
    }
