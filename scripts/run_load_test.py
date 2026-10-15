import sys
import asyncio
import time
import random
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Ensure Windows terminal handles UTF-8 cleanly
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.router.engine import engine
from src.verification.verifier import verifier
from src.database import get_stats, get_connection

TEST_PROMPTS_POOL = {
    "tier_1": [
        "Extract the customer phone number from: Contact Alex at 555-0144 for verification.",
        "Reformat this list into comma separated values: Red, Blue, Green, Yellow, Orange.",
        "Extract invoice ID and due date from: Invoice INV-9042 due on 2026-11-15.",
        "Convert the following string into lowercase: 'AUTHENTICATION_CREDENTIAL_ERROR'.",
        "Parse user status: User ID 4049 is currently marked as ACTIVE in database.",
        "Extract tracking number: Shipped via UPS tracking label 1Z9999999999999999.",
        "Format this date from DD/MM/YYYY to ISO YYYY-MM-DD: 25/12/2026.",
        "Find the IP address in this log: Connection reset by peer from 10.0.0.45 port 8080.",
        "Turn these pairs into a markdown table: Server: A, Ping: 12ms | Server: B, Ping: 34ms.",
        "Extract product code: Model number WH-1000XM5 wireless audio device."
    ],
    "tier_2": [
        "Summarize the quarterly product performance highlights in 3 concise bullet points.",
        "Classify the sentiment of this feedback: 'The application runs smoothly but export feature is slow.'",
        "Draft a polite email confirming attendance at next Tuesday's sprint planning session.",
        "Categorize these support tickets: 1. Password reset 2. Billing dispute 3. Feature question.",
        "Explain the key architectural differences between REST and GraphQL APIs for web clients.",
        "Generate a SQL query to calculate month-over-month active user growth from logins table.",
        "Provide an executive summary of this post-mortem highlighting preventive guardrails.",
        "Outline the pros and cons of implementing client-side caching vs edge CDN caching.",
        "Translate this support notification to Spanish maintaining courteous customer tone.",
        "Draft release notes for version 1.2.0 including bug fixes, security patch, and performance."
    ],
    "tier_3": [
        "Critically evaluate trade-offs between Raft and Byzantine Paxos under split-brain network partitions.",
        "Architect a multi-region distributed streaming telemetry platform with exactly-once idempotency.",
        "Formulate a mathematical proof establishing convergence bounds for stochastic gradient descent on non-convex surfaces.",
        "Perform a deep threat-modeling audit of a zero-knowledge identity rollup against sybil and replay attacks.",
        "Diagnose this complex distributed deadlock involving Postgres row locks, serializable isolation, and foreign keys.",
        "Design a microsecond-latency algorithmic order matching engine with cache-line alignment and lock-free rings.",
        "Analyze legal indemnification exposure in this SaaS master service agreement under Delaware commercial code.",
        "Synthesize a zero-downtime database migration strategy from monolithic Oracle RAC to distributed Spanner."
    ]
}

async def run_load_test(total_requests: int = 500):
    print("=" * 80)
    print(f"PHASE 6: Running Realistic Load Test ({total_requests} Diverse Prompts)")
    print("=" * 80)
    
    verifier.start_worker()
    start_time = time.perf_counter()
    
    # 50% Tier 1, 35% Tier 2, 15% Tier 3 realistic enterprise distribution
    t1_pool = TEST_PROMPTS_POOL["tier_1"]
    t2_pool = TEST_PROMPTS_POOL["tier_2"]
    t3_pool = TEST_PROMPTS_POOL["tier_3"]
    
    batch_size = 25
    for batch_start in range(0, total_requests, batch_size):
        batch_prompts = []
        for _ in range(min(batch_size, total_requests - batch_start)):
            r = random.random()
            if r < 0.50:
                batch_prompts.append(random.choice(t1_pool))
            elif r < 0.85:
                batch_prompts.append(random.choice(t2_pool))
            else:
                batch_prompts.append(random.choice(t3_pool))

        # Execute batch concurrently
        tasks = [engine.route_and_execute(prompt=p) for p in batch_prompts]
        results = await asyncio.gather(*tasks)

        completed_so_far = batch_start + len(results)
        elapsed = time.perf_counter() - start_time
        rps = completed_so_far / max(0.001, elapsed)
        last_meta = results[-1]["routing_metadata"]
        print(f"[{completed_so_far:4d}/{total_requests}] Last Model: {last_meta['selected_model']:16} | Tier: {last_meta['complexity_tier']} | Saved: {last_meta['cost_reduction_pct']:4.1f}% | RPS: {rps:4.1f}", flush=True)

    print("\nWaiting for async verification workers to finish quality scoring...")
    await asyncio.sleep(2.0)
    verifier.stop_worker()

    total_time = time.perf_counter() - start_time
    stats = get_stats()

    print("\n" + "=" * 80)
    print("FINAL PORTFOLIO COST SAVINGS & ROI REPORT")
    print("=" * 80)
    print(f"Total Requests Processed:     {stats['total_requests']}")
    print(f"Total Test Execution Time:    {total_time:.2f} seconds")
    print(f"Overall Routing Throughput:   {stats['total_requests'] / total_time:.1f} req/s")
    print("-" * 80)
    print(f"[$] UNOPTIMIZED COST (All GPT-4o): ${stats['baseline_cost_usd']:.4f}")
    print(f"[*] AUTOPILOT ROUTED COST:         ${stats['total_cost_usd']:.4f}")
    print(f"[+] TOTAL MONEY SAVED:             ${stats['total_saved_usd']:.4f}")
    print(f"[!] HEADLINE COST REDUCTION:       {stats['savings_percentage']}%")
    print("-" * 80)
    print(f"[v] Quality Parity Agreement:    {stats['average_quality_score']:.3f} / 1.000")
    print(f"[x] Auto-Escalation Rate:         {stats['escalation_rate_pct']}%")
    print(f"[>] Average Request Latency:      {stats['average_latency_ms']:.1f} ms")
    print("=" * 80)

if __name__ == "__main__":
    count = 500
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            count = 500
    asyncio.run(run_load_test(count))
