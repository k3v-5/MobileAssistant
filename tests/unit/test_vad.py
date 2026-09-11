import pytest
from core.audio.vad import SimpleEnergyVAD

def test_simple_vad():
    vad = SimpleEnergyVAD(energy_threshold=10)

    # Silence (all zeros or close to 128)
    silence = bytes([128, 128, 128, 128])
    assert not vad.is_speech(silence)

    # High energy
    noise = bytes([0, 255, 0, 255])
    assert vad.is_speech(noise)
