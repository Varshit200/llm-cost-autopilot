from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Message(BaseModel):
    role: str = "user"
    content: str

class ChatCompletionRequest(BaseModel):
    prompt: Optional[str] = None
    messages: Optional[List[Message]] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    model: Optional[str] = None # Optional manual override

class RoutingMetadata(BaseModel):
    selected_model: str
    model_display_name: str
    provider: str
    complexity_tier: str
    complexity_score: float
    reason: str
    latency_ms: float
    cost_usd: float
    baseline_cost_usd: float
    cost_saved_usd: float
    cost_reduction_pct: float

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    output_text: str
    usage: Usage
    routing_metadata: RoutingMetadata

class ModelDetail(BaseModel):
    model_id: str
    display_name: str
    provider: str
    cost_per_input_token: float
    cost_per_output_token: float
    average_latency_ms: float
    quality_tier: str
    description: str

class StatsResponse(BaseModel):
    total_requests: int
    total_cost_usd: float
    baseline_cost_usd: float
    total_saved_usd: float
    savings_percentage: float
    average_latency_ms: float
    average_quality_score: float
    total_escalations: int
    escalation_rate_pct: float
    total_verified: int

class RoutingTierUpdate(BaseModel):
    primary_model: Optional[str] = None
    fallback_model: Optional[str] = None

class RoutingConfigUpdate(BaseModel):
    tier_1: Optional[RoutingTierUpdate] = None
    tier_2: Optional[RoutingTierUpdate] = None
    tier_3: Optional[RoutingTierUpdate] = None
    min_quality_threshold: Optional[float] = None
