import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.classifier.train import train_and_save_classifier

def main():
    print("=" * 60)
    print("Training LLM Complexity Classifier")
    print("=" * 60)
    metrics = train_and_save_classifier()
    print(f"\nModel Accuracy: {metrics['accuracy'] * 100:.2f}%")
    print(f"Total Samples: {metrics['sample_count']} (Held-out Test: {metrics['test_count']})")
    print("\nConfusion Matrix (Rows: Actual, Cols: Predicted):")
    print("             Tier 1   Tier 2   Tier 3")
    labels = ["Tier 1", "Tier 2", "Tier 3"]
    for lbl, row in zip(labels, metrics["confusion_matrix"]):
        print(f"{lbl:8}: {row[0]:8} {row[1]:8} {row[2]:8}")

    print("\nClassification Report:")
    for cls in ["tier_1", "tier_2", "tier_3"]:
        row = metrics["classification_report"][cls]
        print(f"  {cls:8} - Precision: {row['precision']:.2f}, Recall: {row['recall']:.2f}, F1: {row['f1-score']:.2f}")

    print("\nTop Predictive Features:")
    sorted_feats = sorted(metrics["feature_importances"].items(), key=lambda x: x[1], reverse=True)
    for feat, imp in sorted_feats[:5]:
        print(f"  - {feat:20}: {imp:.4f}")

    print(f"\nSaved model artifact to: {metrics['model_path']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
