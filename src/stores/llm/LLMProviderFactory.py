from .LLMEnums import LLMEnums
from .llm.providers import OpenAIProvider, CohereProvider


class LLMProviderFactory:
    def __init__(self, config: dict):
        self.config = config

    def create(self, provider_name: str):
        if provider_name == LLMEnums.OPENAI.value:

            return OpenAIProvider(
                api_key=self.config.OPENAI_API_KEY,
                api_url=self.config.OPENAI_URL,
                default_input_max_tokens=self.config.INPUT_DEFAULT_MAX_TOKENS,
                default_output_max_tokens=self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_temp=self.config.GENERATION_DEFAULT_TEMPERATURE,
            )

        if provider_name == LLMEnums.COHERE.value:
            return CohereProvider(
                api_key=self.config.COHERE_API_KEY,
                default_input_max_tokens=self.config.INPUT_DEFAULT_MAX_TOKENS,
                default_output_max_tokens=self.config.GENERATION_DEFAULT_MAX_TOKENS,
                default_temp=self.config.GENERATION_DEFAULT_TEMPERATURE,
            )
