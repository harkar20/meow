"""
Meowmeow — Bayesian Inference Engine
Takes normalized symptoms + intensity scores and calculates condition probabilities.
Uses a built-in symptom→condition knowledge base (no external CSV needed).
"""

import numpy as np
from typing import Dict, Any, List, Optional

from .nlp_pipeline import extract_symptoms
from .intensity_analyzer import analyze_intensity


import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "clinical_knowledge.db")

# Removed memory-heavy static global load.
# We will query SQLite dynamically for maximum efficiency.



def _compute_scores(
    symptom_icd10_codes: List[str],
    intensity_score: float = 0.5,
) -> List[Dict[str, Any]]:
    """
    Compute posterior-like probability scores for each condition
    given observed symptom ICD-10 codes and intensity.

    Scoring emphasizes:
    1. High-weight symptom matches (a 0.9 match matters more than a 0.3 match)
    2. Number of strong matches (>= 0.6 weight)
    3. Coverage of the condition's key symptoms
    """
    scored = []
    if not symptom_icd10_codes:
        return scored

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create IN clause
    placeholders = ','.join(['?'] * len(symptom_icd10_codes))
    
    # Very fast SQL using pre-aggregated totals table (no correlated subqueries)
    query = f"""
    SELECT c.id, c.name, c.icd10, c.risk_weight, c.patient_explanation, c.doctor_explanation,
           SUM(cs.probability) as matched_weight, 
           COUNT(cs.symptom_code) as matched_count,
           ct.total_weight as max_weight,
           ct.total_symptoms as total_symptoms
    FROM conditions c
    JOIN condition_symptoms cs ON c.id = cs.condition_id
    JOIN condition_totals ct ON c.id = ct.condition_id
    WHERE cs.symptom_code IN ({placeholders})
    GROUP BY c.id
    ORDER BY matched_weight DESC
    LIMIT 50
    """
    
    cursor.execute(query, symptom_icd10_codes)
    candidates = cursor.fetchall()

    for cand in candidates:
        matched_weight = cand["matched_weight"]
        max_possible_weight = cand["max_weight"]
        matched_count = cand["matched_count"]
        total_syms = cand["total_symptoms"]
        
        # We don't have strong_matches explicitly in this fast query unless we do SUM(CASE), 
        # so we will estimate strong_ratio as basically matching
        strong_ratio = matched_weight / max(matched_count * 0.6, 0.1)
        strong_ratio = min(strong_ratio, 1.0)
        
        # Coverage: what fraction of the condition's symptoms were observed
        coverage = matched_count / max(total_syms, 1)

        # Weighted match: how much of the condition's total weight was hit
        weighted_match = matched_weight / max(max_possible_weight, 0.01)

        # Combined formula
        base_score = (weighted_match * 0.5 + strong_ratio * 0.3 + coverage * 0.2)

        # Intensity modifier
        intensity_modifier = 1.0 + (intensity_score - 0.5) * cand["risk_weight"] * 0.5
        final_score = min(base_score * intensity_modifier, 0.98)

        scored.append({
            "name": cand["name"],
            "icd10": cand["icd10"],
            "confidence": round(final_score, 3),
            "matched_symptoms": symptom_icd10_codes,
            "risk_weight": cand["risk_weight"],
            "strong_matches": matched_count,
            "patient_explanation": cand["patient_explanation"],
            "doctor_explanation": cand["doctor_explanation"]
        })

    conn.close()
    scored.sort(key=lambda x: x["confidence"], reverse=True)
    return scored


def _determine_risk_tier(
    top_conditions: List[Dict[str, Any]],
    intensity_score: float,
    is_emergency: bool = False,
) -> str:
    """Determine overall risk tier."""
    if is_emergency:
        return "critical"

    if not top_conditions:
        return "low"

    top = top_conditions[0]
    risk_weight = top.get("risk_weight", 0.2)
    confidence = top.get("confidence", 0.0)

    composite = (risk_weight * 0.5 + confidence * 0.3 + intensity_score * 0.2)

    if composite >= 0.65 or risk_weight >= 0.9:
        return "critical"
    elif composite >= 0.45 or risk_weight >= 0.7:
        return "high"
    elif composite >= 0.30:
        return "medium"
    else:
        return "low"


def _build_reasoning(
    symptoms: List[Dict[str, Any]],
    top_conditions: List[Dict[str, Any]],
    intensity_level: str,
    behavioral_flags: List[str],
    is_emergency: bool = False,
) -> List[str]:
    """Build a human-readable reasoning chain."""
    chain = []

    if is_emergency:
        chain.append("CRITICAL: Emergency keywords detected in patient input. Immediate triage required.")

    # Symptom summary
    symptom_names = [s["normalized_term"] for s in symptoms[:6]]
    if symptom_names:
        chain.append(f"Identified symptoms: {', '.join(symptom_names)}")

    # Intensity note
    chain.append(f"Symptom intensity assessed as {intensity_level}")

    # Top condition reasoning
    if top_conditions:
        top = top_conditions[0]
        matched_count = len(top.get("matched_symptoms", []))
        chain.append(
            f"Primary assessment: {top['name']} (ICD-10: {top['icd10']}) — "
            f"{matched_count} symptom{'s' if matched_count != 1 else ''} matched "
            f"with {top['confidence']*100:.0f}% confidence"
        )

        if len(top_conditions) > 1:
            alts = [f"{c['name']} ({c['confidence']*100:.0f}%)" for c in top_conditions[1:3]]
            chain.append(f"Differential considerations: {', '.join(alts)}")

    # Behavioral note
    if behavioral_flags:
        chain.append(f"Behavioral analysis detected {len(behavioral_flags)} notable signal{'s' if len(behavioral_flags) != 1 else ''}")

    return chain


def _recommended_action(risk_tier: str, top_condition_name: str = "") -> str:
    """Generate recommended action based on risk tier."""
    actions = {
        "critical": "Seek immediate medical attention. Visit the emergency room or call emergency services now.",
        "high": "Contact your healthcare provider urgently. Consider visiting urgent care within the next 6 hours.",
        "medium": "Schedule an appointment with your primary care physician within the next few days. Monitor your symptoms closely.",
        "low": "Continue to monitor your symptoms. If they persist beyond 5-7 days or worsen, schedule a visit with your doctor.",
    }
    return actions.get(risk_tier, actions["low"])


def run_inference(
    text: str,
    answers: Optional[List[Dict[str, str]]] = None,
    behavioral_metadata: Optional[Dict[str, Any]] = None,
    audio_features: Optional[Dict[str, Any]] = None,
    session_history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Full inference pipeline.

    Input:
        text: combined text from all answers
        answers: list of {question, answer} dicts
        behavioral_metadata: from frontend capture
    Output:
        Complete structured risk assessment
    """
    # 1. Symptom extraction
    nlp_result = extract_symptoms(text)
    symptoms = nlp_result["symptoms"]
    icd10_codes = [s["icd10_code"] for s in symptoms]

    # Also extract from individual answers if available
    if answers:
        for qa in answers:
            answer_nlp = extract_symptoms(qa.get("answer", ""))
            for s in answer_nlp["symptoms"]:
                if s["icd10_code"] not in icd10_codes:
                    icd10_codes.append(s["icd10_code"])
                    symptoms.append(s)

    # 2. Intensity analysis
    intensity = analyze_intensity(text, behavioral_metadata, audio_features)

    # 3. Bayesian inference
    condition_scores = _compute_scores(icd10_codes, intensity["intensity_score"])
    top_conditions = condition_scores[:5]

    # 3.5 Emergency check
    emergency_keywords = ["suicide", "kill myself", "chest pain", "can't breathe", "heart attack", "dying", "emergency"]
    is_emergency = any(kw in text.lower() for kw in emergency_keywords)

    # 4. Risk tier
    risk_tier = _determine_risk_tier(top_conditions, intensity["intensity_score"], is_emergency)

    # 5. Behavioral flags
    behavioral_flags = intensity.get("signals_detected", [])
    if is_emergency:
        behavioral_flags.append("EMERGENCY_KEYWORD_DETECTED")

    # 6. Reasoning chain
    reasoning = _build_reasoning(symptoms, top_conditions, intensity["intensity_level"], behavioral_flags, is_emergency)

    top_name = top_conditions[0]["name"] if top_conditions else ""
    action = _recommended_action(risk_tier, top_name)

    # 8. Confidence score
    confidence = top_conditions[0]["confidence"] if top_conditions else 0.3
    
    # 9. Dual Overviews
    patient_exp = top_conditions[0].get("patient_explanation", "") if top_conditions else "We couldn't determine a clear issue right now. It's best to take a rest."
    doctor_exp = top_conditions[0].get("doctor_explanation", "") if top_conditions else "Insufficient symptom alignment for definitive diagnosis."

    # Emergency overrides
    if is_emergency:
        action = "CRITICAL EMERGENCY. CALL EMERGENCY SERVICES IMMEDIATELY (e.g., 911)."
        patient_exp = "EMERGENCY ALERT: Your symptoms suggest a severe and immediately life-threatening situation. Please stop using this app and seek proper emergency medical attention RIGHT NOW."
        doctor_exp = "CRITICAL FLAG: System detected life-threatening keywords (e.g. chest pain, suicide, stroke indicators). Automatic override to max severity. Immediate dispatch to ER recommended."

    return {
        "risk_tier": risk_tier,
        "confidence_score": round(confidence, 3),
        "top_conditions": [
            {"name": c["name"], "confidence": c["confidence"], "icd10": c["icd10"]}
            for c in top_conditions[:5]
        ],
        "reasoning_chain": reasoning,
        "behavioral_flags": behavioral_flags,
        "recommended_action": action,
        "patient_explanation": patient_exp,
        "doctor_explanation": doctor_exp,
        "intensity": intensity,
        "symptoms_extracted": symptoms[:10],
        "categories_detected": nlp_result["categories_detected"],
    }


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = run_inference(
        "I feel really tired all the time and I have been getting headaches and dizziness. "
        "My muscles ache and I can't sleep well.",
        answers=[
            {"question": "How do you feel?", "answer": "I feel exhausted constantly"},
            {"question": "Any pain?", "answer": "yes headaches and body aches"},
        ]
    )
    print(f"Risk Tier: {result['risk_tier']}")
    print(f"Confidence: {result['confidence_score']}")
    print(f"Top conditions:")
    for c in result["top_conditions"]:
        print(f"  - {c['name']} ({c['icd10']}): {c['confidence']*100:.0f}%")
    print(f"\nReasoning:")
    for r in result["reasoning_chain"]:
        print(f"  {r}")
    print(f"\nAction: {result['recommended_action']}")
