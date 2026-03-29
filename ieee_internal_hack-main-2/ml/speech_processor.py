"""
Meowmeow — Speech Processor
Extracts audio features from base64-encoded WAV blobs for intensity analysis.
Uses librosa for RMS energy, speech rate estimation, and MFCC stress indicators.
"""

import base64
import io
import numpy as np
from typing import Dict, Any, Optional

try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


def _decode_audio(audio_base64: str) -> Optional[tuple]:
    """Decode base64 audio to numpy array + sample rate."""
    if not LIBROSA_AVAILABLE:
        return None

    try:
        audio_bytes = base64.b64decode(audio_base64)
        buf = io.BytesIO(audio_bytes)

        # Try soundfile first (handles WAV, FLAC, etc.)
        try:
            data, sr = sf.read(buf)
            if data.ndim > 1:
                data = np.mean(data, axis=1)  # Convert stereo to mono
            return data.astype(np.float32), sr
        except Exception:
            buf.seek(0)
            data, sr = librosa.load(buf, sr=None, mono=True)
            return data, sr
    except Exception:
        return None


def _estimate_speech_rate(y: np.ndarray, sr: int) -> Dict[str, Any]:
    """Estimate speech rate using onset detection as a proxy for syllables."""
    try:
        # Detect onsets (roughly correspond to syllable nuclei)
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, hop_length=512)
        duration = len(y) / sr

        if duration < 0.5:
            return {"syllables_per_sec": 0, "rate_label": "unknown"}

        syllables_per_sec = len(onset_frames) / duration

        if syllables_per_sec > 6:
            label = "rushed"
        elif syllables_per_sec > 4:
            label = "fast"
        elif syllables_per_sec > 2:
            label = "normal"
        elif syllables_per_sec > 0.5:
            label = "slow"
        else:
            label = "very_slow"

        return {
            "syllables_per_sec": round(syllables_per_sec, 2),
            "rate_label": label,
        }
    except Exception:
        return {"syllables_per_sec": 0, "rate_label": "unknown"}


def _extract_stress_indicators(y: np.ndarray, sr: int) -> list:
    """Extract voice stress indicators from MFCCs and spectral features."""
    try:
        indicators = []

        # MFCCs — higher variability in first few coefficients = more emotional speech
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_var = np.var(mfccs, axis=1)

        # High variability in MFCC 1-3 typically indicates stress
        if mfcc_var[1] > 50:
            indicators.append("high_vocal_variability")
        if mfcc_var[2] > 30:
            indicators.append("pitch_instability")

        # Spectral centroid — brighter/sharper voice = more stress
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        mean_centroid = np.mean(centroid)
        if mean_centroid > 2500:
            indicators.append("elevated_vocal_tension")

        # Zero crossing rate — higher ZCR = more noise/breathiness
        zcr = librosa.feature.zero_crossing_rate(y)
        mean_zcr = np.mean(zcr)
        if mean_zcr > 0.15:
            indicators.append("breathiness_detected")

        return indicators
    except Exception:
        return []


def process_audio(audio_base64: str) -> Dict[str, Any]:
    """
    Full audio processing pipeline.

    Input:  base64-encoded audio blob (WAV/WebM from browser MediaRecorder)
    Output: {
        energy_level: float (0.0 - 1.0),
        speech_rate: "slow" | "normal" | "fast" | "rushed",
        stress_indicators: list of str,
        duration_seconds: float,
        features_extracted: bool
    }
    """
    if not LIBROSA_AVAILABLE:
        return {
            "energy_level": 0.5,
            "speech_rate": "normal",
            "stress_indicators": [],
            "duration_seconds": 0,
            "features_extracted": False,
            "note": "librosa not available — install it for audio analysis",
        }

    result = _decode_audio(audio_base64)
    if result is None:
        return {
            "energy_level": 0.5,
            "speech_rate": "normal",
            "stress_indicators": [],
            "duration_seconds": 0,
            "features_extracted": False,
            "note": "Could not decode audio",
        }

    y, sr = result
    duration = len(y) / sr

    # ── RMS Energy ─────────────────────────────────────────────────────────────
    try:
        rms = librosa.feature.rms(y=y)
        mean_rms = float(np.mean(rms))
        # Normalize to 0-1 (typical speech RMS is 0.01 to 0.3)
        energy_level = min(mean_rms / 0.2, 1.0)
    except Exception:
        energy_level = 0.5

    # ── Speech Rate ────────────────────────────────────────────────────────────
    rate_info = _estimate_speech_rate(y, sr)

    # ── Stress Indicators ──────────────────────────────────────────────────────
    stress = _extract_stress_indicators(y, sr)

    return {
        "energy_level": round(energy_level, 3),
        "speech_rate": rate_info["rate_label"],
        "syllables_per_sec": rate_info["syllables_per_sec"],
        "stress_indicators": stress,
        "duration_seconds": round(duration, 2),
        "features_extracted": True,
    }


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Generate a synthetic test audio (sine wave)
    if LIBROSA_AVAILABLE:
        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        # Mix of frequencies to simulate speech
        y = 0.3 * np.sin(2 * np.pi * 200 * t) + 0.1 * np.sin(2 * np.pi * 500 * t)
        y = y.astype(np.float32)

        buf = io.BytesIO()
        sf.write(buf, y, sr, format="WAV")
        audio_b64 = base64.b64encode(buf.getvalue()).decode()

        result = process_audio(audio_b64)
        print(f"Energy: {result['energy_level']}")
        print(f"Speech rate: {result['speech_rate']}")
        print(f"Stress indicators: {result['stress_indicators']}")
        print(f"Duration: {result['duration_seconds']}s")
    else:
        print("librosa not installed — run: pip install librosa soundfile")
