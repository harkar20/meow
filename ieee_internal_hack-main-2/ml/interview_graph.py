"""
Meowmeow — Dynamic Differential Diagnosis Interview Engine (V4)
Generates unique, non-repeating, clinically relevant follow-up questions.

ANTI-REPETITION GUARANTEES:
1. Every generated question string is tracked in session state and NEVER reused.
2. Every symptom ICD code that has been asked about is tracked and excluded.
3. Fallback questions use a fixed ordered pool, not random.choice.
4. The function accepts the FULL history of asked questions and codes.
"""

import random
from typing import Dict, Any, Optional, List, Set
from .nlp_pipeline import extract_symptoms, MEDICAL_TERMS
from .bayesian_engine import _compute_scores, DB_PATH
import sqlite3

TOTAL_QUESTIONS = 50

# ── Ordered clinical question pools (no randomness = no repeats) ──────────────
ONSET_QUESTIONS = [
    "When did you first notice these symptoms?",
    "Did these symptoms come on suddenly or gradually?",
    "How long have you been experiencing this?",
]

SEVERITY_QUESTIONS = [
    ("On a scale of 1 to 10, how severe would you rate your discomfort?",
     [{"value": str(i), "label": f"{i}/10"} for i in range(1, 11)]),
    ("How much is this affecting your daily routine?",
     [{"value": str(i), "label": f"{i}/10"} for i in range(1, 11)]),
    ("Would you say the intensity has been increasing, decreasing, or staying the same?",
     [{"value": "increasing", "label": "Getting worse"},
      {"value": "same", "label": "Staying the same"},
      {"value": "decreasing", "label": "Getting better"}]),
]

CONTEXT_QUESTIONS = [
    "Are you currently taking any medications or supplements?",
    "Do you have any pre-existing medical conditions?",
    "Does anything make the symptoms better or worse?",
    "Have you experienced anything like this before?",
    "Is there anything else you've noticed that you haven't mentioned yet?",
    "Have you traveled anywhere recently?",
    "Has anyone around you been sick recently?",
    "Have you had any recent changes in diet, sleep, or stress levels?",
]


def get_first_question() -> Dict[str, Any]:
    return {
        "question": "In your own words, what's been bothering you? Describe everything you're feeling.",
        "category": "general",
        "depth": 0,
        "branch": "dynamic",
        "total_questions": TOTAL_QUESTIONS,
    }


def get_next_question(
    combined_text: str,
    depth: int,
    asked_symptoms: Optional[List[str]] = None,
    asked_questions: Optional[List[str]] = None,
    asked_fallback_idx: int = 0,
    **kwargs
) -> Dict[str, Any]:
    """
    Produces the next unique, clinically relevant question.
    
    Args:
        combined_text: All patient answers concatenated.
        depth: Current question number (0-indexed).
        asked_symptoms: ICD-10 codes of symptoms already asked about.
        asked_questions: Exact question strings already shown to the user.
        asked_fallback_idx: Index into the ordered fallback pool.
    """
    asked_syms: Set[str] = set(asked_symptoms or [])
    asked_qs: Set[str] = set(asked_questions or [])
    
    if depth >= TOTAL_QUESTIONS:
        return _complete(depth)
    
    # 1. Extract known symptoms
    nlp = extract_symptoms(combined_text)
    icd10_codes = set(s["icd10_code"] for s in nlp["symptoms"])
    
    # Merge: anything the patient mentioned OR we already asked about is OFF LIMITS
    excluded_codes = icd10_codes | asked_syms
    
    # 2. If no symptoms detected yet (depth 1), ask onset
    if not icd10_codes and depth <= 2:
        for q in ONSET_QUESTIONS:
            if q not in asked_qs:
                return _build(q, "onset", depth, asked_fallback_idx)
        # If all onset asked, fall through to context
    
    # 3. Use Bayesian engine to find the best UNIQUE symptom to ask about
    if icd10_codes:
        condition_scores = _compute_scores(list(icd10_codes), 0.5)
        
        if condition_scores:
            top = condition_scores[0]
            # High confidence early stop
            if top["confidence"] > 0.85 and depth > 4:
                return _complete(depth)
            
            # Find the single best symptom we have NOT asked about yet
            best = _find_best_unasked_symptom(
                condition_scores[:5], excluded_codes
            )
            
            if best:
                code, term = best
                question = f"Have you been experiencing any {term} recently?"
                
                # DOUBLE CHECK: if this exact question string was already asked, skip it
                if question not in asked_qs:
                    return _build(question, term, depth, asked_fallback_idx,
                                  symptom_code=code)
    
    # 4. Severity questions (asked in order, depth 2-4 ish)
    for q_text, q_opts in SEVERITY_QUESTIONS:
        if q_text not in asked_qs:
            resp = _build(q_text, "severity", depth, asked_fallback_idx)
            resp["options"] = q_opts
            return resp
    
    # 5. Context/history questions (asked in strict order, never repeated)
    for q in CONTEXT_QUESTIONS:
        if q not in asked_qs:
            return _build(q, "history", depth, asked_fallback_idx + 1)
    
    # 6. If we've exhausted ALL question pools, end the interview
    return _complete(depth)


def _find_best_unasked_symptom(
    candidates: List[Dict[str, Any]], 
    excluded_codes: Set[str]
) -> Optional[tuple]:
    """
    Query SQLite for the highest-value symptom NOT in excluded_codes.
    Returns (icd10_code, human_readable_term) or None.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Collect weighted symptom scores across top candidates
    symptom_weights: Dict[str, float] = {}
    
    for cand in candidates:
        cursor.execute("""
            SELECT symptom_code, probability 
            FROM condition_symptoms
            WHERE condition_id = (
                SELECT id FROM conditions WHERE icd10 = ? LIMIT 1
            )
        """, (cand["icd10"],))
        
        for row in cursor.fetchall():
            code = row["symptom_code"]
            if code not in excluded_codes:
                symptom_weights[code] = (
                    symptom_weights.get(code, 0) 
                    + row["probability"] * cand["confidence"]
                )
    
    conn.close()
    
    if not symptom_weights:
        return None
    
    # Sort by weight descending and pick the top one
    sorted_syms = sorted(symptom_weights.items(), key=lambda x: x[1], reverse=True)
    
    for code, _ in sorted_syms:
        # Map ICD code to human-readable term
        for t in MEDICAL_TERMS:
            if t["icd10"] == code:
                return (code, t["term"])
    
    return None


def _build(
    question: str, category: str, depth: int, 
    fallback_idx: int = 0, symptom_code: str = None
) -> Dict[str, Any]:
    """Build a standard question response dict."""
    resp = {
        "question": question,
        "category": category,
        "depth": depth,
        "branch": "dynamic",
        "total_questions": TOTAL_QUESTIONS,
        "interview_complete": False,
        "fallback_idx": fallback_idx,
    }
    if symptom_code:
        resp["symptom_code"] = symptom_code
    return resp


def _complete(depth: int) -> Dict[str, Any]:
    """Build an interview-complete response."""
    return {
        "question": None,
        "category": None,
        "depth": depth,
        "branch": "dynamic",
        "total_questions": TOTAL_QUESTIONS,
        "interview_complete": True,
    }


if __name__ == "__main__":
    print(get_next_question("my stomach hurts", 1))
    print(get_next_question("my stomach hurts and I am nauseous", 2))
