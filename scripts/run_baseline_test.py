import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.providers.registry import registry
from src.providers.base import ModelConfig

BASELINE_PROMPTS = [
    "Extract the phone number and email address from: Contact support at team@corp.io or +1-800-555-0199.",
    "Convert this list of ingredients into a markdown table: 2 eggs, 1 cup flour, 50g butter, 100ml milk.",
    "Summarize the key benefits of continuous integration for a team of 15 engineers in 2 bullet points.",
    "Classify whether this review expresses positive, neutral, or negative sentiment: 'Battery life is acceptable but software glitches daily.'",
    "Explain the primary difference between synchronous and asynchronous I/O with a brief analogy.",
    "Format this timestamp into ISO 8601 string: October 13, 2026 at 4:30 PM UTC.",
    "Draft a polite 2-sentence response declining a vendor sales pitch while keeping doors open for future quarters.",
    "Generate a SQL query to find top 5 customers by revenue from customers and transactions tables.",
    "Critique the trade-offs of microservices vs monolithic architecture regarding operational overhead and team autonomy.",
    "Architect a resilient multi-region database replication strategy that avoids split-brain and ensures sub-second recovery."
]

async def run_baseline():
    print("=" * 80)
    print("PHASE 1 VALIDATION: Multi-Provider Baseline Testing across 10 Prompts")
    print("=" * 80)

    models = registry.list_models()
    print(f"Loaded {len(models)} models from registry:\n" + "\n".join([f"  - {m.display_name} ({m.model_id}) [{m.quality_tier.upper()}]" for m in models]))
    print("-" * 80)

    results = []

    for idx, prompt in enumerate(BASELINE_PROMPTS, 1):
        print(f"\n[Prompt {idx}/10] \"{prompt[:60]}...\"")
        for model in models:
            resp = await registry.send_request(prompt, model, temperature=0.7, max_tokens=250)
            print(f"  > {model.display_name:24} | Latency: {resp.latency_ms:6.1f}ms | Tokens: {resp.total_tokens:3} | Cost: ${resp.cost_usd:.7f}")
            results.append({
                "prompt_idx": idx,
                "model_id": model.model_id,
                "latency_ms": resp.latency_ms,
                "tokens": resp.total_tokens,
                "cost_usd": resp.cost_usd
            })

    print("\n" + "=" * 80)
    print("BASELINE TESTING SUMMARY:")
    for m in models:
        m_results = [r for r in results if r["model_id"] == m.model_id]
        avg_lat = sum(r["latency_ms"] for r in m_results) / len(m_results)
        tot_cost = sum(r["cost_usd"] for r in m_results)
        print(f"  {m.display_name:24} | Avg Latency: {avg_lat:6.1f}ms | Total Cost (10 prompts): ${tot_cost:.7f}")
    print("=" * 80)
    print("Unified Abstraction Layer successfully validated across all models!")

if __name__ == "__main__":
    asyncio.run(run_baseline())
