from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

@dataclass
class ModelConfig:
    provider: str
    model_id: str
    display_name: str
    cost_per_input_token: float
    cost_per_output_token: float
    average_latency_ms: float
    quality_tier: str  # "high", "medium", "low"
    max_tokens: int = 4096
    description: str = ""

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculates total cost in USD for this model call."""
        cost = (input_tokens * self.cost_per_input_token) + (output_tokens * self.cost_per_output_token)
        return round(cost, 8)


@dataclass
class StandardResponse:
    output_text: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    model_id: str
    provider: str
    raw_response: Optional[Dict[str, Any]] = field(default_factory=dict)


class BaseProvider(ABC):
    @abstractmethod
    async def send_request(
        self,
        prompt: str,
        model_config: ModelConfig,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> StandardResponse:
        """Unified method for dispatching request to provider and returning StandardResponse."""
        pass
