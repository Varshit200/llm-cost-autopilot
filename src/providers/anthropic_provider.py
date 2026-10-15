import time
import httpx
from src.providers.base import BaseProvider, ModelConfig, StandardResponse

class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"

    async def send_request(
        self,
        prompt: str,
        model_config: ModelConfig,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> StandardResponse:
        start_time = time.perf_counter()
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": model_config.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", len(prompt) // 4)
        output_tokens = usage.get("output_tokens", 50)
        total_tokens = input_tokens + output_tokens
        
        output_text = "".join([block.get("text", "") for block in data.get("content", [])])
        cost_usd = model_config.calculate_cost(input_tokens, output_tokens)

        return StandardResponse(
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=cost_usd,
            model_id=model_config.model_id,
            provider="anthropic",
            raw_response=data
        )
