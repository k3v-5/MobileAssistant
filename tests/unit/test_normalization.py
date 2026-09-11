import pytest
from core.nlu.normalization import TranscriptNormalizer

def test_normalization():
    normalizer = TranscriptNormalizer()
    assert normalizer.normalize("Pon me una alarma") == "ponme una alarma"
    assert normalizer.normalize("alas 7") == "a las 7"
    assert normalizer.normalize("¡Hola! ¿qué tal?") == "hola que tal"
    assert normalizer.normalize("  doble   espacio  ") == "doble espacio"
