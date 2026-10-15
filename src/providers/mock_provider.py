import asyncio
import time
import random
from typing import Dict, Any, Optional
from src.providers.base import BaseProvider, ModelConfig, StandardResponse

class MockProvider(BaseProvider):
    """
    High-fidelity simulation provider that generates realistic responses, token counts,
    and latencies. Enables instant out-of-the-box local testing without requiring paid API keys.
    """
    
    def __init__(self, simulate_latency: bool = True):
        self.simulate_latency = simulate_latency

    async def send_request(
        self,
        prompt: str,
        model_config: ModelConfig,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> StandardResponse:
        start_time = time.perf_counter()
        
        # Calculate realistic token metrics
        input_tokens = max(10, int(len(prompt.split()) * 1.35))
        
        # Craft realistic response based on tier and prompt keywords
        lower_prompt = prompt.lower()
        if "json" in lower_prompt or "extract" in lower_prompt:
            output_tokens = random.randint(35, 90)
            sample_output = (
                "{\n"
                '  "status": "success",\n'
                '  "extracted_data": {\n'
                '    "summary": "Automated key-value extraction completed.",\n'
                '    "confidence": 0.98\n'
                "  }\n"
                "}"
            )
        elif "summarize" in lower_prompt or "summary" in lower_prompt:
            output_tokens = random.randint(60, 160)
            sample_output = (
                f"Summary ({model_config.display_name}): The provided context centers on architectural efficiency "
                "and cost optimization across multi-tier LLM clusters. Key takeaways include dynamic routing, "
                "real-time latency tracking, and async evaluation loops."
            )
        elif "analyze" in lower_prompt or "compare" in lower_prompt or "architecture" in lower_prompt:
            output_tokens = random.randint(180, 360)
            sample_output = (
                f"### Comprehensive Multi-Tier Analysis ({model_config.display_name})\n\n"
                "1. **Core Problem Domain**: Large language model overhead can be reduced by 50-85% by steering simple queries away from flagship models.\n"
                "2. **Comparative Trade-offs**: While Tier 3 models excel at reasoning depth, Tier 1 models match quality on 94% of deterministic extraction tasks.\n"
                "3. **Conclusion & Recommendation**: Implement automated verification with auto-escalation thresholds at 0.72 confidence."
            )
        else:
            output_tokens = random.randint(50, 150)
            sample_output = (
                f"Processed response generated via {model_config.display_name}. "
                "The routing layer evaluated your request and fulfilled the prompt requirements with verified fidelity."
            )

        # Simulate realistic latency matching model profile (scaled down slightly for snappy testing)
        target_latency = model_config.average_latency_ms / 1000.0
        actual_delay = max(0.05, random.gauss(target_latency * 0.4, 0.05))
        
        if self.simulate_latency:
            await asyncio.sleep(min(actual_delay, 0.4))
            
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        cost_usd = model_config.calculate_cost(input_tokens, output_tokens)

        return StandardResponse(
            output_text=sample_output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=cost_usd,
            model_id=model_config.model_id,
            provider=f"mock_{model_config.provider}",
            raw_response={"simulated": True, "tier": model_config.quality_tier}
        )
