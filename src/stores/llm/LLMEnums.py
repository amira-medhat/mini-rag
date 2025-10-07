from enum import Enum
from xml.dom.expatbuilder import DOCUMENT_NODE


class LLMEnums(Enum):
    OPENAI = "OPENAI"
    ANTHROPIC = "ANTHROPIC"
    AZURE_OPENAI = "AZURE_OPENAI"
    COHERE = "COHERE"
    AI21 = "AI21"
    HUGGINGFACE = "HUGGINGFACE"
    CUSTOM = "CUSTOM"
    VERTEX_AI = "VERTEX_AI"
    LLM_TYPE_CHAT = "chat"
    LLM_TYPE_COMPLETION = "completion"
    LLM_TYPE_EMBEDDING = "embedding"


class OpenAIEnums(Enum):

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class CohereEnums(Enum):

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "chatbot"
    DOCUMENT = "search_document"
    QUERY = "search_query"


class DocumentTypeEnums(Enum):
    DOCUMENT = "DOCUMENT"
    QUERY = "QUERY"
