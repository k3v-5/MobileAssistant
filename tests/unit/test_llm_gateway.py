import pytest
from pydantic import BaseModel
from providers.llm.local import LocalLLM
from providers.llm.cloud import CloudLLM

class DummySchema(BaseModel):
    dummy_field: str = "test"

@pytest.mark.asyncio
async def test_local_llm():
    llm = LocalLLM()

    gen = await llm.generate("Hello")
    assert "LocalLLM" in gen

    struct = await llm.structured_output("Hello", DummySchema)
    assert isinstance(struct, DummySchema)
    assert struct.dummy_field == "test"

    tokens = llm.count_tokens("Hello world")
    assert tokens == 2

    embeds = await llm.embeddings("Hello")
    assert isinstance(embeds, list)

    chunks = [c async for c in llm.stream("Hello")]
    assert len(chunks) > 0

@pytest.mark.asyncio
async def test_cloud_llm():
    llm = CloudLLM()

    gen = await llm.generate("Hello")
    assert "CloudLLM" in gen

    struct = await llm.structured_output("Hello", DummySchema)
    assert isinstance(struct, DummySchema)

    tokens = llm.count_tokens("Hello world")
    assert tokens == 4 # Cloud mock multiplies by 2

    embeds = await llm.embeddings("Hello")
    assert isinstance(embeds, list)

    chunks = [c async for c in llm.stream("Hello")]
    assert len(chunks) > 0
