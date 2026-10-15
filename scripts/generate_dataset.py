import json
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.config import settings
from src.classifier.features import extract_features

# High quality labeled examples across Tier 1 (Simple), Tier 2 (Moderate), and Tier 3 (Complex)
PROMPTS_DATA = [
    # --- TIER 1: SIMPLE (Reformatting, Extraction, Lookup, Cleanups) ---
    {"tier": "tier_1", "prompt": "Extract the email address from this text: Contact John Doe at john.doe@example.com for questions."},
    {"tier": "tier_1", "prompt": "Convert the following list into a comma-separated single line: Apple, Banana, Orange, Peach."},
    {"tier": "tier_1", "prompt": "Format this phone number into standard international format: 1234567890."},
    {"tier": "tier_1", "prompt": "Extract the total amount and invoice date from this string: Invoice #99182 Dated 2026-10-12 Total Due: $1,450.00."},
    {"tier": "tier_1", "prompt": "Convert this JSON to lowercase keys: {'FirstName': 'Alex', 'LastName': 'Smith'}."},
    {"tier": "tier_1", "prompt": "What is the capital city mentioned in this sentence: Paris is the capital of France and Rome is the capital of Italy?"},
    {"tier": "tier_1", "prompt": "Extract all numbers from this passage: The car drove 45 miles in 50 minutes and burned 2 gallons of fuel."},
    {"tier": "tier_1", "prompt": "Reformat this date from MM/DD/YYYY to YYYY-MM-DD: 11/24/2025."},
    {"tier": "tier_1", "prompt": "Extract the order status from: Order ID 8831 status: DELIVERED to recipient."},
    {"tier": "tier_1", "prompt": "Turn the following key-value pairs into a markdown table: Name: Alice, Age: 30 | Name: Bob, Age: 25."},
    {"tier": "tier_1", "prompt": "Strip all leading and trailing punctuation from the following sentence: ...Hello world!???"},
    {"tier": "tier_1", "prompt": "Find the zip code in this address: 742 Evergreen Terrace, Springfield, OR 97477."},
    {"tier": "tier_1", "prompt": "Extract the flight departure time from: Flight AA102 departs JFK at 08:30 AM EST."},
    {"tier": "tier_1", "prompt": "Given context: The meeting is scheduled for room 4B. Question: Which room is the meeting in?"},
    {"tier": "tier_1", "prompt": "Reformat this raw text into valid JSON with keys name and price: Widget A is $19.99."},
    {"tier": "tier_1", "prompt": "Extract the tracking number from this receipt: FedEx tracking label 99281726154."},
    {"tier": "tier_1", "prompt": "Convert this CSV snippet to JSON array: id,name\\n1,Alpha\\n2,Beta."},
    {"tier": "tier_1", "prompt": "Capitalize the first letter of every word in: the quick brown fox jumps over the lazy dog."},
    {"tier": "tier_1", "prompt": "Extract the IP address from the log entry: 192.168.1.100 - - [10/Oct/2026] GET /index.html 200."},
    {"tier": "tier_1", "prompt": "Check if this string contains the word 'Error': System status: OK, no issues detected."},
    {"tier": "tier_1", "prompt": "Parse this timestamp into ISO-8601 string: 2026-10-13 14:05:00 UTC."},
    {"tier": "tier_1", "prompt": "Given context: Alice is a software engineer. Bob is a product designer. Question: What is Bob's job?"},
    {"tier": "tier_1", "prompt": "Extract currency symbol and numerical value from: €245.50 charged to Mastercard."},
    {"tier": "tier_1", "prompt": "Convert this text into bullet points: We need bread, milk, eggs, and butter."},
    {"tier": "tier_1", "prompt": "Find the HTTP response code in: Server returned status 404 Not Found for resource."},
    {"tier": "tier_1", "prompt": "Reformat the following names to Last, First: Alan Turing, Grace Hopper, Ada Lovelace."},
    {"tier": "tier_1", "prompt": "Extract the error code: Fatal crash EXCEPTION_ACCESS_VIOLATION at address 0x00401000."},
    {"tier": "tier_1", "prompt": "Lookup discount percentage: Promo code SAVE20 provides a 20% discount on cart items."},
    {"tier": "tier_1", "prompt": "Convert this temperature: 72 degrees Fahrenheit to Celsius using formula."},
    {"tier": "tier_1", "prompt": "Extract the product SKU from: Item: Wireless Noise Canceling Headphones, SKU: WN-902-BLK."},

    # --- TIER 2: MODERATE (Summarization, Classification, Structured Analysis) ---
    {"tier": "tier_2", "prompt": "Summarize the following earnings report paragraph in 3 bullet points, highlighting revenue growth and operating margin."},
    {"tier": "tier_2", "prompt": "Classify the sentiment of this customer review as positive, neutral, or negative: The delivery was late but the build quality is decent."},
    {"tier": "tier_2", "prompt": "Draft a professional response to a client inquiring about our Q3 software release timeline."},
    {"tier": "tier_2", "prompt": "Categorize these support tickets into Billing, Technical Support, or Account Inquiries."},
    {"tier": "tier_2", "prompt": "Explain the difference between optimistic and pessimistic locking in relational databases in simple terms."},
    {"tier": "tier_2", "prompt": "Summarize the key findings from this research abstract on sleep cycles and cognitive performance."},
    {"tier": "tier_2", "prompt": "Generate a SQL query to calculate average order value per customer from the orders and customers tables."},
    {"tier": "tier_2", "prompt": "Write a 150-word executive summary of this project post-mortem document focusing on mitigation steps."},
    {"tier": "tier_2", "prompt": "Classify whether this incoming email is spam, sales outreach, or genuine customer correspondence."},
    {"tier": "tier_2", "prompt": "Translate this French customer service announcement to polite and idiomatic English."},
    {"tier": "tier_2", "prompt": "Outline the pros and cons of adopting GraphQL versus REST for a mobile banking application."},
    {"tier": "tier_2", "prompt": "Summarize the key obligations of both parties in this non-disclosure agreement clause."},
    {"tier": "tier_2", "prompt": "Classify the severity level (P1, P2, P3) of this incident ticket based on customer outage descriptions."},
    {"tier": "tier_2", "prompt": "Write an engaging introductory paragraph for a blog post about micro-frontend architecture."},
    {"tier": "tier_2", "prompt": "Describe the main steps required to migrate a monolithic Flask application to FastAPI microservices."},
    {"tier": "tier_2", "prompt": "Summarize this meeting transcript and identify all assigned action items with assignees."},
    {"tier": "tier_2", "prompt": "Categorize these transaction descriptions into budget categories: Groceries, Utilities, Entertainment."},
    {"tier": "tier_2", "prompt": "Provide a structured breakdown of the strengths and weaknesses of Tailwind CSS vs CSS Modules."},
    {"tier": "tier_2", "prompt": "Draft an email thanking a job applicant for interviewing and informing them of the next round."},
    {"tier": "tier_2", "prompt": "Explain how DNS resolution works step-by-step from browser URL entry to IP connection."},
    {"tier": "tier_2", "prompt": "Generate a concise summary of the Federal Reserve's latest interest rate decision statement."},
    {"tier": "tier_2", "prompt": "Classify the intent of this conversational query: 'Where can I find instructions to reset my two-factor auth?'"},
    {"tier": "tier_2", "prompt": "Create an outline for a 30-minute workshop on effective Git branching strategies for junior developers."},
    {"tier": "tier_2", "prompt": "Summarize the plot and thematic motifs of the novel 1984 in under 200 words."},
    {"tier": "tier_2", "prompt": "Write a Python helper function using regex to validate UUIDv4 strings and include unit test assertions."},
    {"tier": "tier_2", "prompt": "Classify this bug report into Frontend, Backend, Database, or DevOps based on the stack trace."},
    {"tier": "tier_2", "prompt": "Synthesize these three customer feedback surveys into top three product roadmap requests."},
    {"tier": "tier_2", "prompt": "Explain the concept of event loop in Node.js and how non-blocking I/O differs from multithreading."},
    {"tier": "tier_2", "prompt": "Summarize the core security principles of Zero Trust Architecture for enterprise IT."},
    {"tier": "tier_2", "prompt": "Draft release notes for version 2.4.0 detailing breaking changes, new features, and deprecation notices."},

    # --- TIER 3: COMPLEX (Deep Multi-step Reasoning, Architecture, Nuance, Proofs) ---
    {"tier": "tier_3", "prompt": "Critically analyze the trade-offs between Paxos and Raft consensus algorithms under asymmetric network partitions, proving safety invariants."},
    {"tier": "tier_3", "prompt": "Architect a fault-tolerant multi-region event-driven telemetry ingestion system handling 5M events/sec with strict idempotency and sub-100ms latency."},
    {"tier": "tier_3", "prompt": "Analyze the legal indemnification clause in this commercial contract to determine exposure to third-party IP infringement damages under California jurisdiction."},
    {"tier": "tier_3", "prompt": "Derive the mathematical proof for convergence in stochastic gradient descent under non-convex loss surfaces, specifying Lipschitz continuity assumptions."},
    {"tier": "tier_3", "prompt": "Diagnose this deadlock scenario in a distributed Postgres cluster involving serializable isolation, row-level locks, and foreign key cascades."},
    {"tier": "tier_3", "prompt": "Evaluate the geopolitical and macroeconomic ramifications of semiconductor export controls across global supply chains over the next decade."},
    {"tier": "tier_3", "prompt": "Design an enterprise Zero-Knowledge Proof (ZKP) identity verification protocol adhering to GDPR compliance and minimal disclosure proofs."},
    {"tier": "tier_3", "prompt": "Write a sophisticated philosophical critique examining deterministic materialism versus emergent dualism in the context of artificial general intelligence."},
    {"tier": "tier_3", "prompt": "Synthesize a comprehensive disaster recovery and business continuity plan for a Tier 1 investment bank following a multi-datacenter ransomware compromise."},
    {"tier": "tier_3", "prompt": "Conduct a deep multi-step root cause analysis on this Linux kernel memory leak stack trace involving slab allocator fragmentation and epoll file descriptors."},
    {"tier": "tier_3", "prompt": "Design an automated market maker (AMM) bonding curve formula that resists sandwich attacks and impermanent loss through dynamic fee adaptation."},
    {"tier": "tier_3", "prompt": "Critique this complex C++20 concurrent lock-free queue implementation, identifying potential ABA race conditions and memory barrier memory order violations."},
    {"tier": "tier_3", "prompt": "Architect an end-to-end LLM orchestration pipeline with speculative decoding, semantic caching, vector indexing, and dynamic guardrail filtering."},
    {"tier": "tier_3", "prompt": "Analyze the biochemical pathway of CRISPR-Cas9 off-target cleavage mechanisms and propose novel guide-RNA structural modifications to maximize specificity."},
    {"tier": "tier_3", "prompt": "Evaluate the ethical, legal, and operational dilemmas of deploying autonomous weapon systems under International Humanitarian Law conventions."},
    {"tier": "tier_3", "prompt": "Formulate a multi-variable game theoretic model predicting pricing equilibrium in an oligopolistic cloud computing market with switching costs."},
    {"tier": "tier_3", "prompt": "Develop a formal verification specification in TLA+ for a distributed two-phase commit transaction manager handling coordinator crashes."},
    {"tier": "tier_3", "prompt": "Perform a rigorous security audit of this smart contract bytecode, identifying reentrancy vulnerabilities, oracle manipulation vectors, and integer overflows."},
    {"tier": "tier_3", "prompt": "Synthesize an overarching cloud migration roadmap for a 30-year-old mainframe core banking ledger to cloud-native microservices with zero downtime."},
    {"tier": "tier_3", "prompt": "Compare and contrast quantum key distribution (QKD) versus post-quantum lattice-based cryptography (Kyber) across implementation complexity, security guarantees, and throughput."}
]

# Programmatically expand dataset to 250+ diverse, realistic examples by varying domain templates
def build_expanded_dataset():
    expanded = list(PROMPTS_DATA)
    
    # Tier 1 generator templates (Simple extraction, formatting, direct lookups)
    t1_templates = [
        "Extract the user ID from: Session token valid for user_id={val} expires at midnight.",
        "Reformat the following product code into uppercase hyphenated syntax: {val}.",
        "Parse the status code and message from: HTTP/1.1 {val} Connection established.",
        "Extract the license plate number from the incident log: Vehicle sighted {val} on highway.",
        "Convert the following string to lowercase: '{val}'.",
        "Extract the monetary value from: Receipt total is {val} including taxes.",
        "Find the domain name in the web address: https://{val}/api/v1/resource.",
        "Given context: {val} is the primary contact. Question: Who should I contact?",
        "Extract the hex color code from this CSS snippet: color: {val}; margin: 0 auto;",
        "Format the following list of items into standard JSON array: {val}."
    ]
    t1_samples = [
        "usr_99182a", "abc49281-prod", "200 OK", "CA-7XY981", "UNEXPECTED_ERROR_OCCURRED",
        "$89.50", "analytics.company-cloud.net", "Dr. Marcus Vance", "#3b82f6", "apple, banana, cherry",
        "usr_00284x", "dev-staging-001", "204 No Content", "NY-849KLL", "AUTHENTICATION_FAILED",
        "$1,200.00", "gateway.payment-provider.com", "Sarah Connor", "#ef4444", "cpu, memory, disk"
    ]
    for i, t in enumerate(t1_templates):
        for s in t1_samples[:8]:
            expanded.append({"tier": "tier_1", "prompt": t.format(val=s)})

    # Tier 2 generator templates (Summaries, Sentiment, Classification, Explanations)
    t2_templates = [
        "Summarize the quarterly performance metrics for {topic} highlighting gross margin and churn.",
        "Classify the tone of the customer message regarding {topic} into frustrated, satisfied, or neutral.",
        "Draft a concise explanation of how {topic} operates for a non-technical stakeholder.",
        "Outline the primary trade-offs between choosing {topic} over traditional relational architectures.",
        "Categorize the following incident regarding {topic} into Priority 1, 2, or 3 based on impact.",
        "Provide a structured 3-paragraph overview of recent advancements in {topic}.",
        "Write a standard operating procedure for onboarding new developers to our {topic} workflow."
    ]
    t2_topics = [
        "customer support SLA compliance", "Apache Kafka event streaming", "Kubernetes pod autoscaling",
        "GraphQL schema federation", "Redis caching eviction policies", "OAuth 2.0 PKCE flow",
        "PostgreSQL query optimization", "CI/CD automated rollback triggers", "Docker multi-stage builds",
        "WebSocket connection pooling", "Snowflake data warehouse partitioning", "Elasticsearch index sharding"
    ]
    for t in t2_templates:
        for top in t2_topics[:10]:
            expanded.append({"tier": "tier_2", "prompt": t.format(topic=top)})

    # Tier 3 generator templates (Deep reasoning, System Architecture, Mathematical proofs, Multi-step analysis)
    t3_templates = [
        "Architect a high-availability distributed architecture for {sys} with Byzantine fault tolerance and formal latency SLA guarantees.",
        "Conduct a comprehensive security threat model and penetration analysis for {sys} under adversarial nation-state capabilities.",
        "Analyze the mathematical derivation and convergence bounds of {sys} under non-convex optimization environments.",
        "Design a multi-region cross-datacenter consensus and state replication engine for {sys} that guarantees strict serializability during split-brain events.",
        "Formulate a formal inductive proof verifying the correctness of {sys} across all concurrent execution traces.",
        "Critique the micro-architectural CPU cache contention and memory barrier ordering in this lock-free implementation of {sys}."
    ]
    t3_systems = [
        "zero-knowledge rollup validation network", "high-frequency algorithmic order execution matching engine",
        "distributed multi-leader Raft replication cluster", "cryptographic threshold signature verification scheme",
        "asynchronous speculative execution hardware pipeline", "autonomous vehicle sensor-fusion Kalman filter pipeline",
        "quantum error-correcting surface code decoder", "decentralized verifiable delay function (VDF) network",
        "multi-tenant kernel-bypass eBPF packet routing fabric", "real-time transactional graph neural network engine"
    ]
    for t in t3_templates:
        for s in t3_systems[:10]:
            expanded.append({"tier": "tier_3", "prompt": t.format(sys=s)})

    # Enrich each record with feature metrics
    final_dataset = []
    for idx, item in enumerate(expanded):
        feats = extract_features(item["prompt"])
        final_dataset.append({
            "id": idx + 1,
            "prompt": item["prompt"],
            "tier": item["tier"],
            "features": feats
        })
    return final_dataset

if __name__ == "__main__":
    dataset = build_expanded_dataset()
    output_path = settings.DATASET_TRAIN_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
    print(f"Generated {len(dataset)} labeled prompt samples across Tier 1, 2, and 3.")
    print(f"Saved dataset to: {output_path}")
