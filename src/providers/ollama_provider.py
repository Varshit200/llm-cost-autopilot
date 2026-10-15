import time
import httpx
from src.providers.base import BaseProvider, ModelConfig, StandardResponse

class OllamaProvider(BaseProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    async def send_request(
        self,
        prompt: str,
        model_config: ModelConfig,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> StandardResponse:
        start_time = time.perf_counter()
        
        payload = {
            "model": model_config.model_id,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Ollama returns prompt_eval_count and eval_count
        input_tokens = data.get("prompt_eval_count", len(prompt) // 4)
        output_tokens = data.get("eval_count", 40)
        total_tokens = input_tokens + output_tokens
        
        output_text = data.get("response", "")
        # Local model has $0.00 cost per token
        cost_usd = model_config.calculate_cost(input_tokens, output_tokens)

        return StandardResponse(
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=cost_usd,
            model_id=model_config.model_id,
            provider="ollama",
            raw_response=data
        )
