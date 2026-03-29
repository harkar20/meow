"""
Meowmeow — Intensity Analyzer
Detects the difference between "it hurts" and "IT HURTS!!" and "it hurts a little maybe."
Multi-signal intensity scoring from text, behavioral metadata, and optional audio features.
"""

import re
from typing import Dict, Any, List, Optional

# ─── Intensifier & Minimizer Lexicons ──────────────────────────────────────────
INTENSIFIERS = [
    "very", "extremely", "incredibly", "really", "so", "terribly", "horribly",
    "excruciating", "unbearable", "severe", "intense", "awful", "terrible",
    "worst", "agonizing", "devastating", "overwhelming", "constant", "nonstop",
    "always", "all the time", "cant stand", "killing me", "dying",
    "absolutely", "completely", "totally", "massive", "enormous",
]

MINIMIZERS = [
    "a little", "slightly", "mildly", "barely", "somewhat", "kind of",
    "sort of", "not that bad", "manageable", "tolerable", "minor",
    "just a bit", "tiny", "small", "occasional", "rarely",
]

HEDGE_WORDS = [
    "maybe", "just", "a little", "probably", "might", "sort of",
    "kind of", "not sure", "i think", "perhaps", "possibly", "i guess",
]

# Clinically significant words that matter if deleted
CLINICAL_DELETION_WORDS = [
    "pain", "hurt", "severe", "bad", "worse", "blood", "bleeding",
    "dying", "kill", "emergency", "help", "extreme", "unbearable",
    "suicide", "depressed", "anxious", "scared", "chest", "heart",
    "breathe", "breathing", "numb", "dizzy", "faint", "vomit",
    "really", "very", "so much", "terrible", "awful", "agony",
]


def _text_signals(text: str) -> Dict[str, Any]:
    """Analyze text-based intensity signals."""
    if not text:
        return {"score": 0.0, "signals": []}

    signals = []
    score = 0.0

    # 1. Uppercase ratio (ignoring short words)
    words = text.split()
    long_words = [w for w in words if len(w) > 2]
    if long_words:
        upper_count = sum(1 for w in long_words if w.isupper())
        upper_ratio = upper_count / len(long_words)
        if upper_ratio > 0.3:
            score += 0.25
            signals.append(f"High uppercase ratio ({upper_ratio:.0%}) — indicates emphasis/distress")
        elif upper_ratio > 0.1:
            score += 0.10
            signals.append(f"Moderate uppercase usage detected")

    # 2. Exclamation / question density
    excl_count = text.count("!")
    if excl_count >= 3:
        score += 0.20
        signals.append(f"Multiple exclamation marks ({excl_count}) — high emphasis")
    elif excl_count >= 1:
        score += 0.08
        signals.append("Exclamation mark usage detected")

    # 3. Word repetition ("hurts hurts hurts")
    lower_words = text.lower().split()
    for i in range(len(lower_words) - 1):
        if lower_words[i] == lower_words[i + 1] and len(lower_words[i]) > 2:
            score += 0.15
            signals.append(f"Word repetition detected: '{lower_words[i]}' — emotional emphasis")
            break

    # 4. Intensifier words
    text_lower = text.lower()
    found_intensifiers = [w for w in INTENSIFIERS if w in text_lower]
    if found_intensifiers:
        intensity_boost = min(len(found_intensifiers) * 0.08, 0.30)
        score += intensity_boost
        signals.append(f"Intensifier words: {', '.join(found_intensifiers[:4])}")

    # 5. Minimizer words (reduce score)
    found_minimizers = [w for w in MINIMIZERS if w in text_lower]
    if found_minimizers:
        score -= min(len(found_minimizers) * 0.06, 0.20)
        signals.append(f"Minimizer words detected: {', '.join(found_minimizers[:3])} — possible downplaying")

    # 6. Hedge words
    found_hedges = [w for w in HEDGE_WORDS if w in text_lower]
    if found_hedges:
        score -= min(len(found_hedges) * 0.04, 0.15)
        signals.append(f"Hedge language detected: {', '.join(found_hedges[:3])} — uncertainty/minimization")

    # 7. Sentence length — very short answers may indicate distress or dismissal
    if len(text.strip()) < 10 and any(w in text_lower for w in ["help", "bad", "dying", "cant"]):
        score += 0.10
        signals.append("Short urgent response detected")

    # 8. ALL CAPS entire message
    if text == text.upper() and len(text) > 10:
        score += 0.15
        signals.append("Entire message in CAPS — high distress signal")

    return {"score": max(score, 0.0), "signals": signals}


def _behavioral_signals(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze behavioral metadata for intensity signals."""
    if not metadata:
        return {"score": 0.0, "signals": []}

    signals = []
    score = 0.0

    # 1. Deleted text analysis
    deleted = metadata.get("deleted_segments", [])
    if deleted:
        # Check if deleted content was clinically significant
        clinical_deletions = []
        for seg in deleted:
            seg_lower = seg.lower()
            for word in CLINICAL_DELETION_WORDS:
                if word in seg_lower:
                    clinical_deletions.append(seg)
                    break

        if clinical_deletions:
            score += 0.20
            signals.append(f"Clinically significant deletions detected ({len(clinical_deletions)} segments) — possible minimization of symptoms")
        elif len(deleted) > 2:
            score += 0.08
            signals.append(f"Multiple text deletions ({len(deleted)}) — hesitation or self-censoring")

    # 2. Typing latency — pauses > 2000ms indicate hesitation
    latencies = metadata.get("typing_latency_ms", [])
    if latencies:
        long_pauses = [l for l in latencies if l > 2000]
        if len(long_pauses) >= 3:
            score += 0.15
            signals.append(f"{len(long_pauses)} significant typing pauses (>2s) — indicates hesitation or emotional processing")
        elif len(long_pauses) >= 1:
            score += 0.06
            signals.append(f"Typing hesitation detected ({len(long_pauses)} pause{'s' if len(long_pauses) > 1 else ''})")

    # 3. Edit count
    edit_count = metadata.get("edit_count", 0)
    if edit_count > 5:
        score += 0.10
        signals.append(f"High edit count ({edit_count}) — difficulty articulating symptoms")
    elif edit_count > 2:
        score += 0.04
        signals.append(f"Moderate editing detected ({edit_count} edits)")

    # 4. Hedge word count from frontend
    hedge_count = metadata.get("hedge_word_count", 0)
    if hedge_count >= 3:
        score -= 0.10
        signals.append(f"High hedge word usage ({hedge_count}) — significant uncertainty or minimization")
    elif hedge_count >= 1:
        score -= 0.04
        signals.append(f"Hedge word usage detected ({hedge_count})")

    return {"score": max(score, 0.0), "signals": signals}


def _audio_signals(audio_features: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze audio features for intensity signals."""
    if not audio_features:
        return {"score": 0.0, "signals": []}

    signals = []
    score = 0.0

    energy = audio_features.get("energy_level", 0.5)
    speech_rate = audio_features.get("speech_rate", "normal")
    stress = audio_features.get("stress_indicators", [])

    if energy > 0.75:
        score += 0.15
        signals.append(f"High vocal energy ({energy:.2f}) — elevated loudness/intensity")
    elif energy < 0.25:
        score += 0.05
        signals.append(f"Low vocal energy ({energy:.2f}) — possible fatigue or withdrawal")

    if speech_rate == "rushed":
        score += 0.10
        signals.append("Rushed speech rate — possible anxiety or urgency")
    elif speech_rate == "slow":
        score += 0.05
        signals.append("Slow speech — possible fatigue or heavy emotional state")

    if stress:
        score += 0.10
        signals.append(f"Voice stress indicators: {', '.join(stress[:3])}")

    return {"score": score, "signals": signals}


def _score_to_level(score: float) -> str:
    """Convert intensity score to categorical level."""
    if score >= 0.70:
        return "critical"
    elif score >= 0.50:
        return "severe"
    elif score >= 0.30:
        return "moderate"
    else:
        return "mild"


def analyze_intensity(
    text: str,
    behavioral_metadata: Optional[Dict[str, Any]] = None,
    audio_features: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Full intensity analysis combining text, behavioral, and audio signals.

    Returns: {
        intensity_score: float (0.0 - 1.0),
        intensity_level: "mild" | "moderate" | "severe" | "critical",
        signals_detected: [str],
        breakdown: { text_score, behavioral_score, audio_score }
    }
    """
    text_result = _text_signals(text)
    behav_result = _behavioral_signals(behavioral_metadata)
    audio_result = _audio_signals(audio_features)

    # Weighted combination
    combined = (
        text_result["score"] * 0.45
        + behav_result["score"] * 0.35
        + audio_result["score"] * 0.20
    )
    # Normalize to 0-1
    final_score = min(max(combined, 0.0), 1.0)

    all_signals = text_result["signals"] + behav_result["signals"] + audio_result["signals"]

    return {
        "intensity_score": round(final_score, 3),
        "intensity_level": _score_to_level(final_score),
        "signals_detected": all_signals,
        "breakdown": {
            "text_score": round(text_result["score"], 3),
            "behavioral_score": round(behav_result["score"], 3),
            "audio_score": round(audio_result["score"], 3),
        },
    }


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        ("it hurts a little maybe", None),
        ("IT HURTS SO MUCH I CANT TAKE IT ANYMORE!!!", None),
        ("my head kind of hurts I guess", {"deleted_segments": ["really bad"], "typing_latency_ms": [100, 3500, 200, 4000], "edit_count": 4, "hedge_word_count": 2}),
        ("help", None),
        ("I feel extremely tired and my body aches terribly all over", None),
    ]
    for text, meta in tests:
        r = analyze_intensity(text, meta)
        print(f"\n─── {text}")
        print(f"  Score: {r['intensity_score']} | Level: {r['intensity_level']}")
        for s in r['signals_detected']:
            print(f"  → {s}")
