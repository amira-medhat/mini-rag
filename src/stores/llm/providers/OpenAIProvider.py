from ..LLMInterface import LLMInterface
from ..LLMEnums import LLMEnums, OpenAIEnums
from openai import OpenAI
import os
import logging


class OpenAIProvider(LLMInterface):

    def __init__(
        self,
        api_key: str,
        default_input_max_tokens: int = 1000,
        default_output_max_tokens: int = 1000,
        default_temp: float = 0.1,
    ):
        self.api_key = api_key
        self.default_input_max_tokens = default_input_max_tokens
        self.default_output_max_tokens = default_output_max_tokens
        self.default_temp = default_temp
        self.generation_model = None
        self.embedding_model = None
        self.embedding_size = None
        self.client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=self.api_key)
        self.enums = OpenAIEnums
        self.logger = logging.getLogger(__name__)

    def process_text(self, text: str):
        return text[: self.default_input_max_tokens].strip()

    def set_generation_model(self, model_id: str):
        self.generation_model = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int = None):
        self.embedding_model = model_id
        self.embedding_size = embedding_size

    def generate_text(
        self,
        prompt: str,
        chat_history: list = [],
        max_output_tokens: int = None,
        temp: float = None,
    ):

        if self.client is None:
            # raise ValueError("OpenAI client is not initialized. Please set the API key and URL.")
            self.logger.error(
                "OpenAI client is not initialized. Please set the API key and URL."
            )
            return None
        if self.generation_model is None:
            # raise ValueError("Generation model is not set. Please set the generation model before generating text.")
            self.logger.error(
                "Generation model is not set. Please set the generation model before generating text."
            )
            return None

        if max_output_tokens is None:
            max_output_tokens = self.default_output_max_tokens
        if temp is None:
            temp = self.default_temp

        chat_history.append(self.construct_prompt(prompt, OpenAIEnums.USER.value))

        response = self.client.chat.completions.create(
            model=self.generation_model,
            messages=chat_history,
            max_tokens=max_output_tokens,
            temperature=temp,
        )

        if (
            not response
            or not response.choices
            or len(response.choices) == 0
            or not response.choices[0].message
        ):
            self.logger.error("Failed to get response from OpenAI.")
            return None

        answer = response.choices[0].message.content.strip()
        chat_history.append(self.construct_prompt(answer, OpenAIEnums.ASSISTANT.value))
        return answer
        # raise NotImplementedError

    def embed_text(self, text: str, document_type: str):
        if self.client is None:
            # raise ValueError("OpenAI client is not initialized. Please set the API key and URL.")
            self.logger.error(
                "OpenAI client is not initialized. Please set the API key and URL."
            )
            return None
        if self.embedding_model is None:
            # raise ValueError("Embedding model is not set. Please set the embedding model before embedding text.")
            self.logger.error(
                "Embedding model is not set. Please set the embedding model before embedding text."
            )
            return None

        response = self.client.embeddings.create(input=text, model=self.embedding_model)

        if (
            not response
            or not response.data
            or len(response.data) == 0
            or not response.data[0].embedding
        ):
            self.logger.error("Failed to get embedding from OpenAI.")
            return None

        return response.data[0].embedding

    def construct_prompt(self, prompt: str, role: str):
        return {"role": role, "content": self.process_text(prompt)}
