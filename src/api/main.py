import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.config import settings
from src.api.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    StatsResponse,
    RoutingConfigUpdate
)
from src.router.engine import engine
from src.providers.registry import registry
from src.verification.verifier import verifier
from src.verification.feedback import feedback_loop
from src.database import get_stats, get_recent_requests, init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("autopilot.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database initialized & verification background worker running
    init_db()
    verifier.start_worker()
    logger.info("LLM Cost Autopilot API initialized and background verifier active.")
    yield
    # Shutdown
    verifier.stop_worker()
    logger.info("LLM Cost Autopilot API stopped.")

app = FastAPI(
    title="LLM Cost Autopilot",
    description="Intelligent multi-model cost optimization routing layer with continuous async verification.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "llm-cost-autopilot",
        "version": settings.VERSION,
        "mode": settings.LLM_PROVIDER_MODE
    }

@app.post(
    "/v1/completions",
    response_model=ChatCompletionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Routing"]
)
async def create_chat_completion(request: ChatCompletionRequest):
    """
    Core Routing Endpoint: Accepts prompt or messages, classifies complexity tier,
    dispatches to the cheapest capable model, benchmarks savings against GPT-4o,
    and returns response with full routing transparency metadata.
    """
    # Extract text from prompt or OpenAI messages array
    prompt_text = request.prompt
    if not prompt_text and request.messages:
        prompt_text = "\n".join([m.content for m in request.messages if m.content])

    if not prompt_text or not prompt_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt text or non-empty messages array is required."
        )

    try:
        result = await engine.route_and_execute(
            prompt=prompt_text,
            temperature=request.temperature or 0.7,
            max_tokens=request.max_tokens or 1000,
            forced_model=request.model
        )
        return result
    except Exception as exc:
        logger.error(f"Routing completion error: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

@app.get("/v1/models", tags=["Configuration"])
async def list_models():
    """Returns list of registered models with cost per token, latency, and quality tier."""
    models = registry.list_models()
    return {
        "models": [
            {
                "model_id": m.model_id,
                "display_name": m.display_name,
                "provider": m.provider,
                "cost_per_input_token": m.cost_per_input_token,
                "cost_per_output_token": m.cost_per_output_token,
                "average_latency_ms": m.average_latency_ms,
                "quality_tier": m.quality_tier,
                "description": m.description
            }
            for m in models
        ]
    }

@app.get("/v1/stats", response_model=StatsResponse, tags=["Analytics"])
async def get_cost_and_quality_stats():
    """Returns aggregated cost savings, baseline GPT-4o comparison, and quality metrics."""
    return get_stats()

@app.get("/v1/routing-config", tags=["Configuration"])
async def get_active_routing_config():
    """Retrieves active routing map and verification thresholds."""
    return settings.get_routing_config()

@app.put("/v1/routing-config", tags=["Configuration"])
async def update_routing_config(updates: RoutingConfigUpdate):
    """
    Hot-updates routing configuration and verification thresholds without server restart.
    """
    cfg = settings.get_routing_config()
    
    if updates.tier_1:
        if updates.tier_1.primary_model:
            cfg["routing"]["tiers"]["tier_1"]["primary_model"] = updates.tier_1.primary_model
        if updates.tier_1.fallback_model:
            cfg["routing"]["tiers"]["tier_1"]["fallback_model"] = updates.tier_1.fallback_model
            
    if updates.tier_2:
        if updates.tier_2.primary_model:
            cfg["routing"]["tiers"]["tier_2"]["primary_model"] = updates.tier_2.primary_model
        if updates.tier_2.fallback_model:
            cfg["routing"]["tiers"]["tier_2"]["fallback_model"] = updates.tier_2.fallback_model

    if updates.tier_3:
        if updates.tier_3.primary_model:
            cfg["routing"]["tiers"]["tier_3"]["primary_model"] = updates.tier_3.primary_model
        if updates.tier_3.fallback_model:
            cfg["routing"]["tiers"]["tier_3"]["fallback_model"] = updates.tier_3.fallback_model

    if updates.min_quality_threshold is not None:
        cfg["verification"]["min_quality_threshold"] = updates.min_quality_threshold

    settings.save_routing_config(cfg)
    registry.reload()
    return {"status": "success", "message": "Routing configuration updated.", "config": cfg}

@app.get("/v1/audit", tags=["Analytics"])
async def get_audit_logs(limit: int = 100):
    """Retrieves recent audit log entries for visualization."""
    return get_recent_requests(limit=limit)

@app.post("/v1/retrain", tags=["Flywheel"])
async def trigger_retraining():
    """
    Ingests accumulated routing failure cases from SQLite audit log,
    retrains the complexity classifier, and hot-reloads runtime predictions.
    """
    try:
        metrics = feedback_loop.retrain_model_with_feedback()
        return {
            "status": "success",
            "message": "Model retrained and hot-reloaded successfully.",
            "metrics": {
                "accuracy": metrics["accuracy"],
                "samples_trained": metrics["sample_count"],
                "feedback_samples_integrated": metrics.get("feedback_samples_integrated", 0)
            }
        }
    except Exception as exc:
        logger.error(f"Retraining error: {exc}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

# Mount ultra-premium Web Dashboard at root /
FRONTEND_DIR = settings.BASE_DIR / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
