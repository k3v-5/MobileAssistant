from typing import Any, AsyncGenerator, List, Type
from pydantic import BaseModel
from providers.llm.provider import LLMProvider

class LocalLLM(LLMProvider):
    """
    Implementation of the LLMProvider for local models (e.g. Ollama, llama.cpp).
    Useful for local intent classification, entity extraction, and small summaries.
    """
    def __init__(self, model_name: str = "llama3-8b"):
        self.model_name = model_name

    async def generate(self, prompt: str) -> str:
        # Placeholder for actual local inference
        return f"[LocalLLM] Mock response to: {prompt[:20]}..."

    async def structured_output(self, prompt: str, schema: Type[BaseModel]) -> BaseModel:
        # Placeholder for local structured inference (e.g. via guidance/outlines)
        return schema()

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:
        yield "[LocalLLM] "
        yield "Streaming "
        yield "Mock "
        yield "Response."

    async def embeddings(self, text: str) -> List[float]:
        # Placeholder for local embeddings
        return [0.0, 0.1, 0.2]

    def count_tokens(self, text: str) -> int:
        # Simple heuristic token counter
        return len(text.split())
