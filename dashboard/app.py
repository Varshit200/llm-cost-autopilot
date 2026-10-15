import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import asyncio
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.config import settings
from src.database import get_stats, get_recent_requests, get_model_distribution, get_connection
from src.router.engine import engine
from src.verification.feedback import feedback_loop

# Page layout and aesthetics

st.set_page_config(
    page_title="LLM Cost Autopilot | Enterprise Routing Layer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern dark / glassmorphism aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .stApp {
        background-color: #07090e;
        background-image: radial-gradient(circle at 15% 15%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                          radial-gradient(circle at 85% 20%, rgba(16, 185, 129, 0.09) 0%, transparent 45%);
    }
    .main-header {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #ffffff 30%, #34d399 70%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }
    .metric-card {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(16, 185, 129, 0.3);
    }
    .hero-metric-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(16, 185, 129, 0.35);
        box-shadow: 0 0 30px rgba(16, 185, 129, 0.15);
    }
    .money-shot {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #34d399, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(16, 185, 129, 0.4);
    }
    .money-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        margin-bottom: 6px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://img.icons8.com/isometric/100/airplane-take-off.png", width=64)
st.sidebar.title("Autopilot Control")
st.sidebar.markdown("**Enterprise LLM Cost Optimization**")

refresh_btn = st.sidebar.button("🔄 Refresh Data", use_container_width=True)
run_flywheel_btn = st.sidebar.button("⚡ Run Retraining Flywheel", use_container_width=True)

if run_flywheel_btn:
    with st.spinner("Analyzing audit failures & retraining classifier..."):
        try:
            res = feedback_loop.retrain_model_with_feedback()
            st.sidebar.success(f"Model Retrained! Acc: {res['accuracy']:.2%} ({res.get('feedback_samples_integrated', 0)} samples added)")
        except Exception as e:
            st.sidebar.error(f"Retrain error: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### Active Routing Tiers")
routing_cfg = settings.get_routing_config().get("routing", {}).get("tiers", {})
for tier_k, tier_v in routing_cfg.items():
    st.sidebar.markdown(f"**{tier_v.get('name')}**: `{tier_v.get('primary_model')}`")

st.sidebar.markdown("---")
st.sidebar.markdown("💡 *Baseline Benchmark:* `GPT-4o`")

# Fetch current KPI stats
stats = get_stats()

# Header
st.markdown('<div class="main-header">⚡ LLM Cost Autopilot</div>', unsafe_allow_html=True)
st.caption("Intelligent routing layer with multi-provider abstraction, Scikit-learn complexity scoring, and continuous async quality validation.")

# --- THE MONEY SHOT & EXECUTIVE METRICS ROW ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card hero-metric-card">
        <div class="money-label">Money Shot Metric: Cost Saved</div>
        <div class="money-shot">{stats['savings_percentage']}%</div>
        <small style="color: #64748b;">vs routing 100% of volume to GPT-4o</small>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="money-label">Total Cost Saved</div>
        <div style="font-size: 2.2rem; font-weight: 700; color: #38bdf8;">${stats['total_saved_usd']:.4f}</div>
        <small style="color: #64748b;">Actual: ${stats['total_cost_usd']:.4f} | Baseline: ${stats['baseline_cost_usd']:.4f}</small>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="money-label">Average Quality Parity</div>
        <div style="font-size: 2.2rem; font-weight: 700; color: #a855f7;">{stats['average_quality_score']:.3f} / 1.0</div>
        <small style="color: #64748b;">Verified: {stats['total_verified']} requests via LLM-as-judge</small>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="money-label">Escalation Rate / Latency</div>
        <div style="font-size: 2.2rem; font-weight: 700; color: #f59e0b;">{stats['escalation_rate_pct']}%</div>
        <small style="color: #64748b;">Avg Latency: {stats['average_latency_ms']:.1f} ms</small>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tabs Navigation
tab_analytics, tab_playground, tab_audit, tab_config = st.tabs([
    "📊 Analytics & Savings",
    "🧪 Live Routing Playground",
    "📝 Request Audit Trail",
    "⚙️ Model Registry & Configuration"
])

# ----------------- TAB 1: ANALYTICS & SAVINGS -----------------
with tab_analytics:
    reqs = get_recent_requests(limit=1000)
    if not reqs:
        st.info("No requests logged yet. Use the 'Live Routing Playground' or run the load test script to populate analytics.")
    else:
        df = pd.DataFrame(reqs)
        
        c1, c2 = st.columns(2)
        
        with c1:
            # 1. Routing Volume Share by Model
            model_counts = df['routed_model'].value_counts().reset_index()
            model_counts.columns = ['Model', 'Requests']
            fig_pie = px.pie(
                model_counts,
                names='Model',
                values='Requests',
                title="Routing Traffic Distribution by Model",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_pie, use_container_width=True)

        with c2:
            # 2. Cumulative Cost vs GPT-4o Baseline
            tier_cost = df.groupby('complexity_tier')[['cost_usd', 'baseline_cost_usd']].sum().reset_index()
            fig_bar = go.Figure(data=[
                go.Bar(name='Autopilot Cost ($)', x=tier_cost['complexity_tier'], y=tier_cost['cost_usd'], marker_color='#10b981'),
                go.Bar(name='Unoptimized GPT-4o Cost ($)', x=tier_cost['complexity_tier'], y=tier_cost['baseline_cost_usd'], marker_color='#ef4444')
            ])
            fig_bar.update_layout(
                barmode='group',
                title="Spend by Complexity Tier: Autopilot vs Unoptimized Baseline",
                xaxis_title="Complexity Tier",
                yaxis_title="Total Spend (USD)",
                margin=dict(t=40, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        c3, c4 = st.columns(2)
        
        with c3:
            # 3. Quality Score Distribution
            verified_df = df[df['quality_score'].notnull()]
            if not verified_df.empty:
                fig_hist = px.histogram(
                    verified_df,
                    x='quality_score',
                    nbins=20,
                    title="Async Quality Verification Agreement Score Distribution",
                    color='complexity_tier',
                    labels={'quality_score': 'Agreement Score (0.0 to 1.0)'}
                )
                fig_hist.update_layout(margin=dict(t=40, b=20, l=20, r=20))
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("Quality verifications are processing asynchronously.")

        with c4:
            # 4. Latency vs Cost Reduction
            fig_scatter = px.scatter(
                df,
                x='latency_ms',
                y='cost_reduction_pct',
                color='complexity_tier',
                size='total_tokens',
                hover_data=['routed_model', 'request_id'],
                title="Latency (ms) vs Cost Savings (%) per Request",
                labels={'latency_ms': 'Latency (ms)', 'cost_reduction_pct': 'Cost Savings (%)'}
            )
            fig_scatter.update_layout(margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_scatter, use_container_width=True)

# ----------------- TAB 2: LIVE ROUTING PLAYGROUND -----------------
with tab_playground:
    st.subheader("Test Prompt Complexity Classification & Dynamic Routing")
    st.write("Submit any prompt to see the classifier determine complexity, extract features, and route to the optimal model.")

    preset = st.selectbox(
        "Choose a sample test prompt or type custom text below:",
        [
            "Custom Prompt",
            "[Tier 1 - Simple] Extract the email address and phone number from: Contact support at help@cloudops.io or call 555-0199.",
            "[Tier 1 - Simple] Reformat this list of names into a standard JSON array: Alice, Bob, Charlie, Dana.",
            "[Tier 2 - Moderate] Summarize this quarterly product update in 3 concise bullet points with key metrics.",
            "[Tier 2 - Moderate] Classify whether this user feedback is positive, negative, or neutral: 'The UI is snappy but docs are confusing.'",
            "[Tier 3 - Complex] Architect a distributed fault-tolerant multi-region database replication pipeline with strict serializability under network split-brain scenarios.",
            "[Tier 3 - Complex] Formulate a formal mathematical proof for stochastic gradient descent convergence on non-convex manifolds with Lipschitz gradients."
        ]
    )

    if preset == "Custom Prompt":
        default_val = "Extract the order ID and delivery date from: Receipt #88491 scheduled for 2026-11-04."
    else:
        default_val = preset.split("] ")[1] if "] " in preset else preset

    user_prompt = st.text_area("Prompt Input:", value=default_val, height=120)
    
    col_btn, col_opt = st.columns([1, 2])
    with col_btn:
        route_btn = st.button("🚀 Route & Execute Prompt", type="primary", use_container_width=True)
    with col_opt:
        model_override = st.selectbox(
    "Optional Manual Model Override:",
    ["Auto-Route (Recommended)"] +
    [m["model_id"] for m in settings.get_models_config().values()]
)


    if route_btn and user_prompt.strip():
        with st.spinner("Analyzing complexity and routing to optimal provider..."):
            forced = None if model_override == "Auto-Route (Recommended)" else model_override
            res = asyncio.run(engine.route_and_execute(prompt=user_prompt, forced_model=forced))
            
            meta = res["routing_metadata"]
            
            st.success(f"Routed Successfully! **{meta['model_display_name']}** selected.")
            
            pcol1, pcol2, pcol3, pcol4 = st.columns(4)
            pcol1.metric("Predicted Tier", meta["complexity_tier"].upper(), f"Score: {meta['complexity_score']:.2f}")
            pcol2.metric("Execution Cost", f"${meta['cost_usd']:.6f}", f"-{meta['cost_reduction_pct']}% saved")
            pcol3.metric("GPT-4o Baseline Cost", f"${meta['baseline_cost_usd']:.6f}")
            pcol4.metric("Latency", f"{meta['latency_ms']:.1f} ms")

            st.markdown("#### Model Response:")
            st.code(res["output_text"], language="markdown")

            st.markdown("#### Routing Justification & Audit Metadata:")
            st.json(meta)

# ----------------- TAB 3: REQUEST AUDIT TRAIL -----------------
with tab_audit:
    st.subheader("Auditing & Verification Ledger")
    st.write("Complete per-request ledger containing token metrics, pricing, verification agreement, and auto-escalation flags.")
    
    all_reqs = get_recent_requests(limit=150)
    if all_reqs:
        audit_df = pd.DataFrame(all_reqs)
        # Select key columns for clean table display
        cols = [
            'request_id', 'timestamp', 'complexity_tier', 'routed_model',
            'cost_usd', 'baseline_cost_usd', 'cost_saved_usd', 'cost_reduction_pct',
            'latency_ms', 'quality_score', 'is_escalated'
        ]
        available_cols = [c for c in cols if c in audit_df.columns]
        st.dataframe(audit_df[available_cols], use_container_width=True)
    else:
        st.info("No audit logs found yet.")

# ----------------- TAB 4: MODEL REGISTRY & CONFIGURATION -----------------
with tab_config:
    st.subheader("Model Registry & Active Pricing Table")
    models_cfg = settings.get_models_config()
    model_rows = []
    for k, v in models_cfg.items():
        model_rows.append({
            "Model ID": v.get("model_id"),
            "Display Name": v.get("display_name"),
            "Provider": v.get("provider"),
            "Tier": v.get("quality_tier").upper(),
            "Input Cost ($ / 1M)": f"${v.get('cost_per_input_token') * 1_000_000:.2f}",
            "Output Cost ($ / 1M)": f"${v.get('cost_per_output_token') * 1_000_000:.2f}",
            "Avg Latency (ms)": v.get("average_latency_ms"),
            "Description": v.get("description")
        })
    st.table(pd.DataFrame(model_rows))
