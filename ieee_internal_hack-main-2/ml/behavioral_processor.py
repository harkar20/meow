"""
Meowmeow — Behavioral Signal Processor
Analyzes HOW the user typed — not just WHAT they typed.
Processes keystroke timing, deletions, and hedge language.
"""

import re
from typing import Dict, Any, List, Optional

# Clinically significant words (if deleted = possible minimization)
CLINICAL_WORDS = {
    "pain", "hurt", "hurts", "ache", "aching", "severe", "bad", "worse", "worst",
    "blood", "bleeding", "dying", "kill", "emergency", "help", "extreme",
    "unbearable", "excruciating", "suicide", "depressed", "anxious", "scared",
    "terrified", "chest", "heart", "breathe", "breathing", "numb", "dizzy",
    "faint", "vomit", "really", "very", "so much", "terrible", "awful",
    "agony", "constant", "always", "never stops",
}

HEDGE_WORDS = {
    "maybe", "just", "a little", "probably", "might", "sort of",
    "kind of", "not sure", "i think", "perhaps", "possibly", "i guess",
    "not really", "barely", "somewhat",
}

EMOTIONAL_WORDS = {
    "scared", "terrified", "afraid", "worried", "anxious", "panic",
    "hopeless", "desperate", "overwhelmed", "crying", "devastated",
    "angry", "frustrated", "confused", "lost",
}


def _analyze_typing_latency(latencies: List[int]) -> Dict[str, Any]:
    """Analyze typing patterns from keystroke latencies."""
    if not latencies:
        return {"mean_latency_ms": 0, "hesitation_events": 0, "typing_speed": "unknown", "flags": []}

    import numpy as np
    arr = np.array(latencies, dtype=float)

    mean_lat = float(np.mean(arr))
    std_lat = float(np.std(arr)) if len(arr) > 1 else 0.0
    hesitations = int(np.sum(arr > 2000))
    long_pauses = int(np.sum(arr > 5000))

    flags = []
    speed = "normal"

    if mean_lat > 500:
        speed = "slow"
        flags.append("Slow overall typing speed — possible fatigue or careful word selection")
    elif mean_lat < 100:
        speed = "fast"
        flags.append("Very fast typing — possible urgency or agitation")

    if hesitations >= 3:
        flags.append(f"{hesitations} significant pauses (>2s) — emotional processing or difficulty articulating")
    elif hesitations >= 1:
        flags.append(f"{hesitations} typing pause{'s' if hesitations > 1 else ''} detected")

    if long_pauses >= 1:
        flags.append(f"{long_pauses} extended pause{'s' if long_pauses > 1 else ''} (>5s) — strong hesitation signal")

    # Check for speed changes within the response
    if len(arr) > 10:
        first_half = np.mean(arr[:len(arr)//2])
        second_half = np.mean(arr[len(arr)//2:])
        if second_half > first_half * 2:
            flags.append("Typing slowed significantly mid-response — possible emotional difficulty")
        elif first_half > second_half * 2:
            flags.append("Typing accelerated mid-response — possible rush to finish or anxiety")

    return {
        "mean_latency_ms": round(mean_lat, 1),
        "hesitation_events": hesitations,
        "typing_speed": speed,
        "flags": flags,
    }


def _analyze_deletions(deleted_segments: List[str]) -> Dict[str, Any]:
    """Analyze deleted text for clinical significance."""
    if not deleted_segments:
        return {"clinical_significance": "none", "deleted_clinical_words": [], "flags": []}

    flags = []
    clinical_deletions = []
    emotional_deletions = []

    for seg in deleted_segments:
        seg_lower = seg.lower().strip()
        if not seg_lower:
            continue

        # Check for clinical word deletions
        for word in CLINICAL_WORDS:
            if word in seg_lower:
                clinical_deletions.append(seg)
                break

        # Check for emotional word deletions
        for word in EMOTIONAL_WORDS:
            if word in seg_lower:
                emotional_deletions.append(seg)
                break

    significance = "none"
    if clinical_deletions:
        significance = "high"
        flags.append(
            f"Patient deleted clinically significant content ({len(clinical_deletions)} instance{'s' if len(clinical_deletions) > 1 else ''}) — "
            f"possible minimization of symptoms"
        )
    elif emotional_deletions:
        significance = "moderate"
        flags.append(
            f"Patient deleted emotional content ({len(emotional_deletions)} instance{'s' if len(emotional_deletions) > 1 else ''}) — "
            f"possible suppression of emotional distress"
        )
    elif len(deleted_segments) > 3:
        significance = "low"
        flags.append(f"Multiple text deletions ({len(deleted_segments)}) — difficulty expressing symptoms")

    return {
        "clinical_significance": significance,
        "deleted_clinical_words": [s[:50] for s in clinical_deletions],
        "deleted_emotional_words": [s[:50] for s in emotional_deletions],
        "total_deletions": len(deleted_segments),
        "flags": flags,
    }


def _analyze_hedge_language(text: str) -> Dict[str, Any]:
    """Detect hedge language in the answer text."""
    if not text:
        return {"hedge_count": 0, "hedges_found": [], "flags": []}

    text_lower = text.lower()
    found = [h for h in HEDGE_WORDS if h in text_lower]
    flags = []

    if len(found) >= 3:
        flags.append(f"Heavy hedge language ({len(found)} instances: {', '.join(found[:4])}) — significant uncertainty or symptom minimization")
    elif len(found) >= 1:
        flags.append(f"Hedge language detected ({', '.join(found)}) — possible minimization")

    return {
        "hedge_count": len(found),
        "hedges_found": found,
        "flags": flags,
    }


def process_behavioral_signals(
    answer_text: str,
    deleted_segments: Optional[List[str]] = None,
    keystroke_timestamps: Optional[List[int]] = None,
    typing_latency_ms: Optional[List[int]] = None,
    edit_count: int = 0,
    hedge_word_count: int = 0,
    session_id: str = "",
) -> Dict[str, Any]:
    """
    Full behavioral signal processing.

    Input: answer text + frontend metadata
    Output: comprehensive behavioral profile
    """
    # Use typing_latency_ms directly if available, otherwise compute from timestamps
    latencies = typing_latency_ms or []
    if not latencies and keystroke_timestamps and len(keystroke_timestamps) > 1:
        latencies = [keystroke_timestamps[i] - keystroke_timestamps[i-1]
                     for i in range(1, len(keystroke_timestamps))]

    # Run analyses
    latency_analysis = _analyze_typing_latency(latencies)
    deletion_analysis = _analyze_deletions(deleted_segments or [])
    hedge_analysis = _analyze_hedge_language(answer_text)

    # Compile all flags
    all_flags = (
        latency_analysis["flags"]
        + deletion_analysis["flags"]
        + hedge_analysis["flags"]
    )

    # Overall behavioral concern level
    concern_score = 0.0
    if deletion_analysis["clinical_significance"] == "high":
        concern_score += 0.35
    elif deletion_analysis["clinical_significance"] == "moderate":
        concern_score += 0.20

    if latency_analysis["hesitation_events"] >= 3:
        concern_score += 0.25
    elif latency_analysis["hesitation_events"] >= 1:
        concern_score += 0.10

    if hedge_analysis["hedge_count"] >= 3:
        concern_score += 0.20
    elif hedge_analysis["hedge_count"] >= 1:
        concern_score += 0.08

    if edit_count > 5:
        concern_score += 0.15
    elif edit_count > 2:
        concern_score += 0.05

    concern_level = "none"
    if concern_score >= 0.50:
        concern_level = "high"
    elif concern_score >= 0.25:
        concern_level = "moderate"
    elif concern_score > 0:
        concern_level = "low"

    return {
        "session_id": session_id,
        "behavioral_concern_level": concern_level,
        "behavioral_concern_score": round(min(concern_score, 1.0), 3),
        "typing_analysis": latency_analysis,
        "deletion_analysis": deletion_analysis,
        "hedge_analysis": hedge_analysis,
        "edit_count": edit_count,
        "all_flags": all_flags,
    }


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = process_behavioral_signals(
        answer_text="I maybe have a little headache, I think. It's probably nothing.",
        deleted_segments=["really bad pain", "I'm scared"],
        keystroke_timestamps=[0, 150, 300, 3500, 3650, 3800, 8000, 8150, 8300],
        edit_count=4,
        hedge_word_count=3,
    )
    print(f"Concern Level: {result['behavioral_concern_level']}")
    print(f"Concern Score: {result['behavioral_concern_score']}")
    print(f"\nFlags:")
    for f in result["all_flags"]:
        print(f"  → {f}")
