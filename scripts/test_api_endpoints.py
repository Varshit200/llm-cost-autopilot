import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from src.api.main import app

def test_api():
    client = TestClient(app)
    
    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("PASS: /health endpoint")

    # 2. Models list
    res = client.get("/v1/models")
    assert res.status_code == 200
    models = res.json()["models"]
    assert len(models) >= 5
    print(f"PASS: /v1/models (found {len(models)} models)")

    # 3. Stats endpoint
    res = client.get("/v1/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "savings_percentage" in stats
    print(f"PASS: /v1/stats (Savings: {stats['savings_percentage']}%, Total: {stats['total_requests']} requests)")

    # 4. Completions routing endpoint (Simple Tier 1 prompt)
    prompt_simple = "Extract the order number from this text: Order #4481 was placed successfully."
    res = client.post("/v1/completions", json={"prompt": prompt_simple})
    assert res.status_code == 200, f"Completions failed: {res.text}"
    data = res.json()
    assert data["routing_metadata"]["complexity_tier"] == "tier_1"
    assert data["routing_metadata"]["cost_reduction_pct"] > 70.0
    print(f"PASS: /v1/completions Tier 1 -> Model: {data['routing_metadata']['selected_model']}, Saved: {data['routing_metadata']['cost_reduction_pct']}%")

    # 5. Completions routing endpoint (Complex Tier 3 prompt)
    prompt_complex = "Critically analyze the mathematical convergence bounds of stochastic gradient descent and architect a distributed consensus engine with Byzantine fault tolerance."
    res = client.post("/v1/completions", json={"prompt": prompt_complex})
    assert res.status_code == 200
    data = res.json()
    assert data["routing_metadata"]["complexity_tier"] == "tier_3"
    print(f"PASS: /v1/completions Tier 3 -> Model: {data['routing_metadata']['selected_model']}")

    # 6. Routing config endpoint
    res = client.get("/v1/routing-config")
    assert res.status_code == 200
    print("PASS: /v1/routing-config GET")

    print("\n" + "=" * 50)
    print("ALL API ENDPOINT INTEGRATION TESTS PASSED 100%!")
    print("=" * 50)

if __name__ == "__main__":
    test_api()
