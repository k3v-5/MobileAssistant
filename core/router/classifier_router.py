from typing import Dict, Optional
from core.contracts import Intent, ExecutionMode

class ClassifierRouter:
    """
    Second-stage router in the pipeline.
    Used when deterministic rules fail or confidence is medium.
    Uses basic semantic/keyword clustering to classify intent execution mode.
    """
    def __init__(self, high_confidence_threshold: float = 0.85, low_confidence_threshold: float = 0.5):
        self.high_threshold = high_confidence_threshold
        self.low_threshold = low_confidence_threshold

        # Keyword clustering for basic classification fallback
        self.clusters: Dict[str, ExecutionMode] = {
            "alarma": ExecutionMode.DIRECT,
            "volumen": ExecutionMode.DIRECT,
            "brillo": ExecutionMode.DIRECT,
            "wifi": ExecutionMode.DIRECT,

            "youtube": ExecutionMode.WORKFLOW,
            "spotify": ExecutionMode.WORKFLOW,

            "resume": ExecutionMode.AGENT,
            "busca": ExecutionMode.WORKFLOW,
            "resumen": ExecutionMode.AGENT,
        }

    def route(self, intent: Intent, text: Optional[str] = None) -> ExecutionMode:
        """
        Classifies execution mode.
        If intent confidence is very high, trust the classification.
        If low, fallback to LLM.
        If in between, use text clustering to guess.
        """
        # If confidence is extremely low, immediate fallback to LLM reasoning
        if intent.confidence < self.low_threshold:
            return ExecutionMode.LLM

        # If we have a medium confidence intent but know the text, try clustering
        if text and intent.confidence < self.high_threshold:
            text_lower = text.lower()
            for keyword, mode in self.clusters.items():
                if keyword in text_lower:
                    return mode

        # Otherwise, if confidence is high, but deterministic router didn't catch it,
        # fallback to LLM since we don't have a rigid rule for it.
        return ExecutionMode.LLM
