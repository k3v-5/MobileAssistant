from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, List, Type
from pydantic import BaseModel

class LLMProvider(ABC):
    """
    Abstract Base Class defining the LLM Gateway interface.
    Keeps the core system agnostic to whether OpenAI, Ollama, Gemini, etc. is used.
    """

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generates a text response from the given prompt."""
        pass

    @abstractmethod
    async def structured_output(self, prompt: str, schema: Type[BaseModel]) -> BaseModel:
        """Generates a structured output adhering to the provided Pydantic schema."""
        pass

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streams the text response from the given prompt."""
        pass

    @abstractmethod
    async def embeddings(self, text: str) -> List[float]:
        """Generates vector embeddings for the given text."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Counts the number of tokens in the given text."""
        pass
