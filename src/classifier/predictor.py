import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
from src.config import settings
from src.classifier.features import extract_features, features_to_vector
from src.classifier.train import train_and_save_classifier

logger = logging.getLogger("autopilot.classifier.predictor")

class ComplexityPredictor:
    def __init__(self, model_path: Path = None):
        self.model_path = model_path or settings.CLASSIFIER_MODEL_PATH
        self.model = None
        self.scaler = None
        self.classes = None
        self.metadata = {}
        self.load_or_train()

    def load_or_train(self):
        if not self.model_path.exists():
            logger.info(f"Model file not found at {self.model_path}. Initiating training...")
            result = train_and_save_classifier(output_path=self.model_path)
            logger.info(f"Classifier trained successfully with accuracy: {result['accuracy']:.2%}")

        package = joblib.load(self.model_path)
        self.model = package["model"]
        self.scaler = package["scaler"]
        self.classes = list(package["classes"])
        self.metadata = {
            "accuracy": package.get("accuracy"),
            "feature_importances": package.get("feature_importances"),
            "confusion_matrix": package.get("confusion_matrix")
        }

    def predict(self, prompt: str) -> Dict[str, Any]:
        """
        Analyzes prompt and predicts complexity tier, score, and feature diagnostics.
        """
        feats = extract_features(prompt)
        vec = features_to_vector(feats).reshape(1, -1)
        vec_scaled = self.scaler.transform(vec)

        probabilities = self.model.predict_proba(vec_scaled)[0]
        prob_dict = {cls_name: float(prob) for cls_name, prob in zip(self.classes, probabilities)}

        predicted_tier = self.classes[int(np.argmax(probabilities))]
        
        # Calculate continuous complexity score (0.0 to 1.0)
        # Weighting: tier_1=0.15, tier_2=0.55, tier_3=0.95
        p1 = prob_dict.get("tier_1", 0.0)
        p2 = prob_dict.get("tier_2", 0.0)
        p3 = prob_dict.get("tier_3", 0.0)
        complexity_score = round(p1 * 0.15 + p2 * 0.55 + p3 * 0.95, 3)

        return {
            "tier": predicted_tier,
            "complexity_score": complexity_score,
            "probabilities": prob_dict,
            "features": feats
        }

# Global singleton instance
predictor = ComplexityPredictor()
