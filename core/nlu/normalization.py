import re

class TranscriptNormalizer:
    """
    Normalizes transcript text to unify formatting and simplify intent detection.
    Does not alter semantics, only normalizes structure (e.g. "pon me" -> "ponme").
    """
    def __init__(self):
        # Basic mapping of common dictation errors or splits
        self.replacements = {
            r"\bpon me\b": "ponme",
            r"\ba las\b": "a las",
            r"\balas\b": "a las", # "alas 7" -> "a las 7"
            r"qué": "que",
            r"á": "a",
            r"é": "e",
            r"í": "i",
            r"ó": "o",
            r"ú": "u",
        }

    def normalize(self, text: str) -> str:
        """
        Normalizes the given transcript text.
        """
        normalized = text.lower().strip()

        # Remove common punctuation that doesn't add semantic value for routing
        normalized = re.sub(r'[¿?¡!,.]', '', normalized)

        for pattern, replacement in self.replacements.items():
            normalized = re.sub(pattern, replacement, normalized)

        # Clean up double spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized
