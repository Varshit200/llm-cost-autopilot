import uuid
from datetime import datetime, timezone
import logging
from typing import Dict, Any, Optional
from src.config import settings
from src.providers.base import ModelConfig, StandardResponse
from src.providers.registry import registry
from src.classifier.predictor import predictor
from src.verification.verifier import verifier
from src.database import log_request, compute_prompt_hash

logger = logging.getLogger("autopilot.router")

class RoutingEngine:
    def __init__(self):
        self.registry = registry
        self.predictor = predictor
        self.verifier = verifier

    def select_model_for_tier(self, tier: str) -> ModelConfig:
        """Determines best model config from active routing YAML."""
        routing_cfg = settings.get_routing_config()
        tier_cfg = routing_cfg.get("routing", {}).get("tiers", {}).get(tier, {})
        
        primary_model_id = tier_cfg.get("primary_model")
        model = self.registry.get_model(primary_model_id) if primary_model_id else None

        if not model:
            fallback_id = tier_cfg.get("fallback_model")
            model = self.registry.get_model(fallback_id) if fallback_id else None

        if not model:
            # Safe default fallback
            model = self.registry.get_model("gpt-4o-mini") or self.registry.list_models()[0]

        return model

    async def route_and_execute(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        forced_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        End-to-end routing pipeline:
        1. Classifies prompt complexity.
        2. Routes to cheapest capable model.
        3. Executes request with latency & cost calculation.
        4. Benchmarks cost against frontier baseline (GPT-4o).
        5. Logs structured audit trail into SQLite.
        6. Enqueues async verification loop.
        """
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        prompt_hash = compute_prompt_hash(prompt)

        # 1. Complexity classification
        classification = self.predictor.predict(prompt)
        tier = classification["tier"]
        complexity_score = classification["complexity_score"]

        # 2. Model selection
        if forced_model:
            selected_model = self.registry.get_model(forced_model)
            if not selected_model:
                raise ValueError(f"Forced model '{forced_model}' is not registered.")
            routing_reason = f"Manual override to {selected_model.display_name}."
        else:
            selected_model = self.select_model_for_tier(tier)
            routing_reason = (
                f"Classified as {tier.upper()} (score: {complexity_score:.2f}). "
                f"Routed to optimal cost model: {selected_model.display_name}."
            )

        # 3. Model execution
        response: StandardResponse = await self.registry.send_request(
            prompt=prompt,
            model_config=selected_model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # 4. Benchmark baseline cost calculation (reference model: GPT-4o)
        routing_cfg = settings.get_routing_config()
        ref_model_id = routing_cfg.get("benchmark", {}).get("reference_model", "gpt-4o")
        reference_model = self.registry.get_model(ref_model_id) or selected_model

        baseline_cost = reference_model.calculate_cost(response.input_tokens, response.output_tokens)
        cost_saved = max(0.0, baseline_cost - response.cost_usd)
        savings_pct = (cost_saved / baseline_cost * 100.0) if baseline_cost > 0 else 0.0

        # Truncated prompt preview
        prompt_preview = prompt if len(prompt) <= 250 else prompt[:247] + "..."

        # 5. SQLite Audit Logging
        log_payload = {
            "request_id": request_id,
            "timestamp": timestamp,
            "prompt_preview": prompt_preview,
            "prompt_hash": prompt_hash,
            "complexity_tier": tier,
            "complexity_score": complexity_score,
            "routed_model": selected_model.model_id,
            "routed_provider": selected_model.provider,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.total_tokens,
            "cost_usd": response.cost_usd,
            "baseline_model": reference_model.model_id,
            "baseline_cost_usd": baseline_cost,
            "cost_saved_usd": round(cost_saved, 8),
            "cost_reduction_pct": round(savings_pct, 2),
            "latency_ms": response.latency_ms,
            "quality_score": None,
            "verified": 0,
            "is_escalated": 0,
            "escalation_reason": None,
            "output_text": response.output_text,
            "is_retrain_sample": 0
        }
        log_request(log_payload)

        # 6. Asynchronous Quality Verification Enqueue (zero latency impact)
        await self.verifier.enqueue_verification(
            request_id=request_id,
            prompt=prompt,
            routed_model=selected_model.model_id,
            output_text=response.output_text,
            complexity_tier=tier
        )

        return {
            "id": request_id,
            "object": "chat.completion",
            "created": int(datetime.now(timezone.utc).timestamp()),
            "output_text": response.output_text,
            "usage": {
                "prompt_tokens": response.input_tokens,
                "completion_tokens": response.output_tokens,
                "total_tokens": response.total_tokens
            },
            "routing_metadata": {
                "selected_model": selected_model.model_id,
                "model_display_name": selected_model.display_name,
                "provider": selected_model.provider,
                "complexity_tier": tier,
                "complexity_score": complexity_score,
                "reason": routing_reason,
                "latency_ms": response.latency_ms,
                "cost_usd": response.cost_usd,
                "baseline_cost_usd": baseline_cost,
                "cost_saved_usd": round(cost_saved, 6),
                "cost_reduction_pct": round(savings_pct, 1)
            }
        }

engine = RoutingEngine()
