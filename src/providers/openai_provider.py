import time
import httpx
from typing import Optional
from src.providers.base import BaseProvider, ModelConfig, StandardResponse

class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"

    async def send_request(
        self,
        prompt: str,
        model_config: ModelConfig,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> StandardResponse:
        start_time = time.perf_counter()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_config.model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", len(prompt) // 4)
        output_tokens = usage.get("completion_tokens", 50)
        total_tokens = input_tokens + output_tokens
        
        output_text = data["choices"][0]["message"]["content"]
        cost_usd = model_config.calculate_cost(input_tokens, output_tokens)

        return StandardResponse(
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=cost_usd,
            model_id=model_config.model_id,
            provider="openai",
            raw_response=data
        )
