from typing import Dict
from core.contracts import Intent, ExecutionMode

class RuleBasedRouter:
    """
    Deterministically routes intents to their corresponding execution modes.
    Follows the architecture principle: only use LLMs when strictly necessary.
    """
    def __init__(self):
        # Maps intent names to their required ExecutionMode
        self.rules: Dict[str, ExecutionMode] = {
            "open_app": ExecutionMode.DIRECT,
            "close_app": ExecutionMode.DIRECT,
            "create_alarm": ExecutionMode.DIRECT,
            "delete_alarm": ExecutionMode.DIRECT,
            "set_volume": ExecutionMode.DIRECT,
            "set_brightness": ExecutionMode.DIRECT,
            "toggle_wifi": ExecutionMode.DIRECT,
            "toggle_bluetooth": ExecutionMode.DIRECT,

            "search_youtube": ExecutionMode.WORKFLOW,
            "play_music": ExecutionMode.WORKFLOW,
            "morning_routine": ExecutionMode.WORKFLOW,

            "summarize_video": ExecutionMode.AGENT,
            "find_invoice": ExecutionMode.AGENT,
            "complex_query": ExecutionMode.LLM,
        }

    def route(self, intent: Intent) -> ExecutionMode:
        """
        Determines the execution mode for a given intent based on strict rules.
        Defaults to LLM fallback if the intent is not recognized.
        """
        if intent.confidence < 0.6:
            # If we are not confident in the intent, fall back to LLM reasoning
            return ExecutionMode.LLM

        return self.rules.get(intent.name, ExecutionMode.LLM)
