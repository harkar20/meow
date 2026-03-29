"""
Meowmeow — Temporal Trajectory Model
Compares current session symptom vector to past visits
to detect escalating, improving, or stable patterns.
"""

import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime


# Body system categories for tracking scope expansion
SYSTEM_CATEGORIES = {
    "fatigue": "general/systemic",
    "pain": "musculoskeletal",
    "respiratory": "respiratory",
    "digestive": "gastrointestinal",
    "neurological": "neurological",
    "mood": "psychiatric",
    "dermatological": "dermatological",
    "cardiovascular": "cardiovascular",
    "urinary": "genitourinary",
}


def _encode_symptoms(icd10_codes: List[str]) -> np.ndarray:
    """Create a fixed-length binary vector from ICD-10 codes."""
    # Use a hash-based encoding for a fixed vector size
    VECTOR_SIZE = 64
    vec = np.zeros(VECTOR_SIZE)
    for code in icd10_codes:
        idx = hash(code) % VECTOR_SIZE
        vec[idx] = 1.0
    return vec


def _get_systems(categories: List[str]) -> set:
    """Map symptom categories to body systems."""
    systems = set()
    for cat in categories:
        system = SYSTEM_CATEGORIES.get(cat, cat)
        systems.add(system)
    return systems


def analyze_trajectory(
    session_history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Analyze temporal trajectory across sessions.

    Input: list of session dicts, each with:
        - session_date: ISO datetime string
        - symptom_icd10_codes: list of ICD-10 strings
        - risk_tier: str
        - intensity_score: float
        - categories: list of str (symptom categories)

    The LAST item in the list is the current session.

    Output: {
        trajectory_label: "stable" | "worsening" | "improving" | "new_onset",
        escalation_score: float (0.0 - 1.0),
        new_systems_involved: list of new body system names,
        comparison: { ... details ... }
    }
    """
    if not session_history or len(session_history) < 2:
        return {
            "trajectory_label": "new_onset",
            "escalation_score": 0.0,
            "new_systems_involved": [],
            "comparison": {"note": "First visit — no prior data for comparison"},
        }

    current = session_history[-1]
    previous_sessions = session_history[:-1]

    # ── Symptom count trajectory ───────────────────────────────────────────────
    current_codes = set(current.get("symptom_icd10_codes", []))
    all_past_codes = set()
    for s in previous_sessions:
        all_past_codes.update(s.get("symptom_icd10_codes", []))

    new_symptoms = current_codes - all_past_codes
    resolved_symptoms = all_past_codes - current_codes

    # ── Intensity trajectory ───────────────────────────────────────────────────
    current_intensity = current.get("intensity_score", 0.5)
    past_intensities = [s.get("intensity_score", 0.5) for s in previous_sessions]
    avg_past_intensity = np.mean(past_intensities) if past_intensities else 0.5
    intensity_change = current_intensity - avg_past_intensity

    # ── Risk tier trajectory ───────────────────────────────────────────────────
    tier_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    current_tier_val = tier_map.get(current.get("risk_tier", "low"), 1)
    past_tier_vals = [tier_map.get(s.get("risk_tier", "low"), 1) for s in previous_sessions]
    avg_past_tier = np.mean(past_tier_vals) if past_tier_vals else 1
    tier_change = current_tier_val - avg_past_tier

    # ── System scope expansion ─────────────────────────────────────────────────
    current_systems = _get_systems(current.get("categories", []))
    past_systems = set()
    for s in previous_sessions:
        past_systems.update(_get_systems(s.get("categories", [])))

    new_systems = list(current_systems - past_systems)

    # ── Compute escalation score ───────────────────────────────────────────────
    escalation = 0.0

    # New symptoms appearing
    if len(new_symptoms) > 0:
        escalation += min(len(new_symptoms) * 0.10, 0.30)

    # Intensity increasing
    if intensity_change > 0.15:
        escalation += 0.25
    elif intensity_change > 0.05:
        escalation += 0.10

    # Risk tier increasing
    if tier_change > 0.5:
        escalation += 0.20
    elif tier_change > 0:
        escalation += 0.10

    # New body systems involved
    if new_systems:
        escalation += min(len(new_systems) * 0.15, 0.30)

    # Improving signals (reduce escalation)
    if len(resolved_symptoms) > len(new_symptoms):
        escalation -= 0.20
    if intensity_change < -0.15:
        escalation -= 0.15
    if tier_change < -0.5:
        escalation -= 0.15

    escalation = max(min(escalation, 1.0), 0.0)

    # ── Determine trajectory label ─────────────────────────────────────────────
    if escalation >= 0.45:
        label = "worsening"
    elif escalation <= 0.10 and (intensity_change < -0.1 or len(resolved_symptoms) > 0):
        label = "improving"
    else:
        label = "stable"

    return {
        "trajectory_label": label,
        "escalation_score": round(escalation, 3),
        "new_systems_involved": new_systems,
        "comparison": {
            "new_symptoms_count": len(new_symptoms),
            "resolved_symptoms_count": len(resolved_symptoms),
            "intensity_change": round(intensity_change, 3),
            "tier_change": round(tier_change, 3),
            "sessions_compared": len(previous_sessions),
        },
    }


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    history = [
        {
            "session_date": "2025-03-20",
            "symptom_icd10_codes": ["R53.83", "R51.9"],
            "risk_tier": "low",
            "intensity_score": 0.3,
            "categories": ["fatigue", "pain"],
        },
        {
            "session_date": "2025-03-25",
            "symptom_icd10_codes": ["R53.83", "R51.9", "R42", "R06.00"],
            "risk_tier": "medium",
            "intensity_score": 0.55,
            "categories": ["fatigue", "pain", "neurological", "respiratory"],
        },
    ]
    result = analyze_trajectory(history)
    print(f"Trajectory: {result['trajectory_label']}")
    print(f"Escalation: {result['escalation_score']}")
    print(f"New systems: {result['new_systems_involved']}")
    print(f"Details: {result['comparison']}")
