import pytest
from core.contracts import Intent, ExecutionMode
from core.router.rule_router import RuleBasedRouter

def test_rule_based_router():
    router = RuleBasedRouter()

    # Test high confidence deterministic match
    intent_alarm = Intent(name="create_alarm", confidence=0.9)
    assert router.route(intent_alarm) == ExecutionMode.DIRECT

    # Test high confidence workflow match
    intent_youtube = Intent(name="search_youtube", confidence=0.85)
    assert router.route(intent_youtube) == ExecutionMode.WORKFLOW

    # Test low confidence falls back to LLM despite known intent name
    intent_low_conf = Intent(name="create_alarm", confidence=0.5)
    assert router.route(intent_low_conf) == ExecutionMode.LLM

    # Test unknown intent falls back to LLM
    intent_unknown = Intent(name="unknown_intent", confidence=0.9)
    assert router.route(intent_unknown) == ExecutionMode.LLM
