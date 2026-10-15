import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from src.config import settings
from src.classifier.features import extract_features
from src.classifier.train import train_and_save_classifier
from src.classifier.predictor import predictor
from src.database import get_retrain_candidates

logger = logging.getLogger("autopilot.verification.feedback")

FEEDBACK_FILE = settings.DATA_DIR / "feedback_retrain_data.json"

class FeedbackLoop:
    def __init__(self):
        self.feedback_file = FEEDBACK_FILE

    def collect_feedback_from_db(self) -> int:
        """Collects routing failure candidates from the audit database."""
        candidates = get_retrain_candidates()
        if not candidates:
            return 0

        existing_feedback = self.load_feedback()
        existing_hashes = {item["prompt_hash"] for item in existing_feedback}
        
        added = 0
        for cand in candidates:
            p_hash = cand["prompt_hash"]
            if p_hash not in existing_hashes:
                # Elevate tier: if it failed at tier_1, upgrade to tier_2 or tier_3
                current_tier = cand["complexity_tier"]
                elevated_tier = "tier_2" if current_tier == "tier_1" else "tier_3"
                
                existing_feedback.append({
                    "prompt": cand["prompt_preview"],
                    "prompt_hash": p_hash,
                    "original_tier": current_tier,
                    "tier": elevated_tier,
                    "quality_score": cand["quality_score"],
                    "escalation_reason": cand["escalation_reason"]
                })
                existing_hashes.add(p_hash)
                added += 1

        if added > 0:
            with open(self.feedback_file, "w", encoding="utf-8") as f:
                json.dump(existing_feedback, f, indent=2)

        return added

    def load_feedback(self) -> List[Dict[str, Any]]:
        if not self.feedback_file.exists():
            return []
        try:
            with open(self.feedback_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def retrain_model_with_feedback(self) -> Dict[str, Any]:
        """
        Flywheel retraining: Combines original training dataset with accumulated
        failure feedback, retrains the Scikit-learn classifier, and hot-reloads runtime predictor.
        """
        self.collect_feedback_from_db()
        
        # Load baseline dataset
        with open(settings.DATASET_TRAIN_PATH, "r", encoding="utf-8") as f:
            base_data = json.load(f)

        feedback_data = self.load_feedback()
        logger.info(f"Retraining triggered with {len(base_data)} base samples + {len(feedback_data)} feedback samples.")

        combined = list(base_data)
        for fb in feedback_data:
            combined.append({
                "prompt": fb["prompt"],
                "tier": fb["tier"],
                "features": extract_features(fb["prompt"])
            })

        # Save merged dataset temporarily
        temp_merged = settings.DATA_DIR / "dataset_merged.json"
        with open(temp_merged, "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2)

        # Retrain classifier
        metrics = train_and_save_classifier(dataset_path=temp_merged, output_path=settings.CLASSIFIER_MODEL_PATH)
        
        # Hot-reload global predictor
        predictor.load_or_train()
        logger.info("Classifier hot-reloaded successfully with feedback updates.")

        metrics["feedback_samples_integrated"] = len(feedback_data)
        return metrics

feedback_loop = FeedbackLoop()
