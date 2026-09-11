import pytest
from core.contracts import Intent, ExecutionMode
from core.router.classifier_router import ClassifierRouter

def test_classifier_router():
    router = ClassifierRouter()

    # Low confidence falls back to LLM
    intent_low = Intent(name="unknown", confidence=0.4)
    assert router.route(intent_low) == ExecutionMode.LLM

    # Medium confidence with known keyword
    intent_med = Intent(name="unknown", confidence=0.7)
    assert router.route(intent_med, text="ponme una alarma") == ExecutionMode.DIRECT

    # Medium confidence with different keyword
    assert router.route(intent_med, text="resume el video") == ExecutionMode.AGENT

    # High confidence (not caught by deterministic rule, hits classifier)
    # The default for high confidence missing from deterministic is LLM
    intent_high = Intent(name="some_new_intent", confidence=0.9)
    assert router.route(intent_high) == ExecutionMode.LLM
