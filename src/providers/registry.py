import logging
from typing import Dict, List, Optional
from src.config import settings
from src.providers.base import ModelConfig, StandardResponse, BaseProvider
from src.providers.openai_provider import OpenAIProvider
from src.providers.anthropic_provider import AnthropicProvider
from src.providers.ollama_provider import OllamaProvider
from src.providers.mock_provider import MockProvider

logger = logging.getLogger("autopilot.providers")

class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, ModelConfig] = {}
        self._alias_map: Dict[str, str] = {}
        self._mock_provider = MockProvider()
        self._openai_provider: Optional[OpenAIProvider] = None
        self._anthropic_provider: Optional[AnthropicProvider] = None
        self._ollama_provider: Optional[OllamaProvider] = None
        self.reload()

    def reload(self):
        """Reload models and initialize providers."""
        raw_models = settings.get_models_config()
        self._models.clear()
        self._alias_map.clear()

        for key, data in raw_models.items():
            cfg = ModelConfig(
                provider=data.get("provider", "mock"),
                model_id=data.get("model_id", key),
                display_name=data.get("display_name", key),
                cost_per_input_token=float(data.get("cost_per_input_token", 0.0)),
                cost_per_output_token=float(data.get("cost_per_output_token", 0.0)),
                average_latency_ms=float(data.get("average_latency_ms", 500.0)),
                quality_tier=data.get("quality_tier", "medium"),
                max_tokens=int(data.get("max_tokens", 4096)),
                description=data.get("description", "")
            )
            self._models[key] = cfg
            self._alias_map[cfg.model_id] = key

        # Init live providers if keys exist
        if settings.OPENAI_API_KEY:
            self._openai_provider = OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        else:
            self._openai_provider = None

        if settings.ANTHROPIC_API_KEY:
            self._anthropic_provider = AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self._anthropic_provider = None

        self._ollama_provider = OllamaProvider(base_url=settings.OLLAMA_BASE_URL)

    def get_model(self, model_id_or_key: str) -> Optional[ModelConfig]:
        if model_id_or_key in self._models:
            return self._models[model_id_or_key]
        if model_id_or_key in self._alias_map:
            key = self._alias_map[model_id_or_key]
            return self._models.get(key)
        # Search by prefix or loose match
        for key, cfg in self._models.items():
            if model_id_or_key.lower() in key.lower() or model_id_or_key.lower() in cfg.model_id.lower():
                return cfg
        return None

    def list_models(self) -> List[ModelConfig]:
        return list(self._models.values())

    async def send_request(
        self,
        prompt: str,
        model_config: ModelConfig,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> StandardResponse:
        """
        Unified dispatch across OpenAI, Anthropic, Ollama, and Mock providers.
        Gracefully falls back to Mock simulation if live API keys are not supplied.
        """
        mode = settings.LLM_PROVIDER_MODE
        
        # If simulation mode is explicitly configured
        if mode == "simulation":
            return await self._mock_provider.send_request(prompt, model_config, temperature, max_tokens)

        # Provider routing
        try:
            if model_config.provider == "openai":
                if self._openai_provider:
                    return await self._openai_provider.send_request(prompt, model_config, temperature, max_tokens)
                elif mode == "auto":
                    logger.info(f"OpenAI key not set, using high-fidelity mock for {model_config.model_id}")
                    return await self._mock_provider.send_request(prompt, model_config, temperature, max_tokens)
                else:
                    raise ValueError("OPENAI_API_KEY is not configured and live mode is active.")

            elif model_config.provider == "anthropic":
                if self._anthropic_provider:
                    return await self._anthropic_provider.send_request(prompt, model_config, temperature, max_tokens)
                elif mode == "auto":
                    logger.info(f"Anthropic key not set, using high-fidelity mock for {model_config.model_id}")
                    return await self._mock_provider.send_request(prompt, model_config, temperature, max_tokens)
                else:
                    raise ValueError("ANTHROPIC_API_KEY is not configured and live mode is active.")

            elif model_config.provider == "ollama":
                try:
                    if self._ollama_provider and mode != "simulation":
                        return await self._ollama_provider.send_request(prompt, model_config, temperature, max_tokens)
                except Exception as e:
                    if mode == "auto":
                        logger.info(f"Ollama server unavailable ({e}), using mock for {model_config.model_id}")
                        return await self._mock_provider.send_request(prompt, model_config, temperature, max_tokens)
                    raise

            # Fallback to mock provider
            return await self._mock_provider.send_request(prompt, model_config, temperature, max_tokens)

        except Exception as exc:
            if mode == "auto":
                logger.warning(f"Error calling live provider ({exc}). Falling back to mock response.")
                return await self._mock_provider.send_request(prompt, model_config, temperature, max_tokens)
            raise

registry = ModelRegistry()

async def send_request(
    prompt: str,
    model_config: ModelConfig,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> StandardResponse:
    """Convenience functional interface for send_request."""
    return await registry.send_request(prompt, model_config, temperature, max_tokens)
