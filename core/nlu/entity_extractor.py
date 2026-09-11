import re
from typing import Dict, Any

class EntityExtractor:
    """
    Extracts entities (like dates, times, labels) from normalized text.
    Uses regex patterns as a baseline, falling back to LLMs when necessary (in later phases).
    """

    def __init__(self):
        # Time mapping
        self.time_words = {
            "una": "01:00",
            "dos": "02:00",
            "tres": "03:00",
            "cuatro": "04:00",
            "cinco": "05:00",
            "seis": "06:00",
            "siete": "07:00",
            "ocho": "08:00",
            "nueve": "09:00",
            "diez": "10:00",
            "once": "11:00",
            "doce": "12:00",
        }

        self.minute_words = {
            "y cuarto": "15",
            "y media": "30",
            "menos cuarto": "45"
        }

    def extract(self, text: str, intent_name: str) -> Dict[str, Any]:
        """
        Extract entities based on the intent context.
        """
        entities = {}

        if intent_name == "create_alarm":
            # Extract date
            if "mañana" in text:
                entities["date"] = "tomorrow"
            elif "hoy" in text:
                entities["date"] = "today"

            # Extract time
            time_match = re.search(r'a las ([\w\s]+?)(?:\sque diga|\s$|$)', text)
            if time_match:
                time_str = time_match.group(1).strip()
                entities["time"] = self._parse_time(time_str)

            # Extract label
            label_match = re.search(r'que diga (.*)', text)
            if label_match:
                entities["label"] = label_match.group(1).strip()

        return entities

    def _parse_time(self, time_str: str) -> str:
        """
        Parses a time string like "siete y cuarto" to "07:15".
        """
        base_time = "00:00"

        # Check base hour
        for word, t in self.time_words.items():
            if time_str.startswith(word):
                base_time = t
                break

        # Check minutes
        for word, m in self.minute_words.items():
            if word in time_str:
                if word == "menos cuarto":
                    # Adjust hour down - basic implementation
                    hour = int(base_time[:2]) - 1
                    if hour <= 0: hour = 12
                    base_time = f"{hour:02d}:45"
                else:
                    base_time = base_time[:3] + m
                break

        return base_time
