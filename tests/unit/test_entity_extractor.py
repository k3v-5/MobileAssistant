import pytest
from core.nlu.entity_extractor import EntityExtractor

def test_entity_extractor_alarm():
    extractor = EntityExtractor()
    text = "ponme una alarma mañana a las siete y cuarto que diga gimnasio"

    entities = extractor.extract(text, "create_alarm")

    assert entities.get("date") == "tomorrow"
    assert entities.get("time") == "07:15"
    assert entities.get("label") == "gimnasio"

def test_entity_extractor_alarm_menos_cuarto():
    extractor = EntityExtractor()
    text = "ponme una alarma hoy a las ocho menos cuarto que diga despertar"

    entities = extractor.extract(text, "create_alarm")

    assert entities.get("date") == "today"
    assert entities.get("time") == "07:45"
    assert entities.get("label") == "despertar"
