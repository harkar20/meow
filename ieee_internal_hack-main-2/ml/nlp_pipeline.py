"""
Meowmeow — NLP Pipeline
Medical symptom extraction + ICD-10 normalization from raw user text.
Uses keyword dictionary + fuzzy matching (no heavy model downloads).
"""

from thefuzz import fuzz
from typing import List, Dict, Any
import re

# ─── Medical Term Dictionary ───────────────────────────────────────────────────
# Each entry: { canonical_name, icd10, category, aliases[] }
MEDICAL_TERMS: List[Dict[str, Any]] = [
    # ── Fatigue / General ──────────────────────────────────────────────────────
    {"term": "fatigue",            "icd10": "R53.83", "category": "fatigue",       "aliases": ["tired", "exhausted", "no energy", "worn out", "drained", "run down", "lethargic", "sluggish", "weary"]},
    {"term": "malaise",            "icd10": "R53.81", "category": "fatigue",       "aliases": ["feel off", "not right", "unwell", "generally unwell", "just off", "feel weird", "feel bad", "feel awful"]},
    {"term": "weakness",           "icd10": "R53.1",  "category": "fatigue",       "aliases": ["weak", "feeble", "no strength", "cant lift", "muscles weak"]},
    {"term": "insomnia",           "icd10": "G47.00", "category": "fatigue",       "aliases": ["cant sleep", "no sleep", "sleep problems", "trouble sleeping", "awake at night", "sleepless", "tossing and turning"]},
    {"term": "excessive sleepiness","icd10": "R40.0",  "category": "fatigue",       "aliases": ["sleeping too much", "always sleeping", "hypersomnia", "oversleep"]},
    {"term": "fever",              "icd10": "R50.9",  "category": "fatigue",       "aliases": ["temperature", "hot", "burning up", "feverish", "chills and fever", "running a temp"]},
    {"term": "chills",             "icd10": "R68.83", "category": "fatigue",       "aliases": ["shivering", "cold sweats", "freezing", "goosebumps"]},
    {"term": "night sweats",       "icd10": "R61",    "category": "fatigue",       "aliases": ["sweating at night", "wake up sweating", "drenched in sweat"]},
    {"term": "weight loss",        "icd10": "R63.4",  "category": "fatigue",       "aliases": ["losing weight", "lost weight", "getting thin", "unintentional weight loss"]},
    {"term": "weight gain",        "icd10": "R63.5",  "category": "fatigue",       "aliases": ["gaining weight", "put on weight", "getting heavier"]},
    {"term": "appetite loss",      "icd10": "R63.0",  "category": "fatigue",       "aliases": ["no appetite", "not hungry", "cant eat", "dont want to eat", "loss of appetite"]},

    # ── Pain ───────────────────────────────────────────────────────────────────
    {"term": "headache",           "icd10": "R51.9",  "category": "pain",          "aliases": ["head hurts", "head pain", "head ache", "head pounding", "migraine", "throbbing head", "head pressure"]},
    {"term": "chest pain",         "icd10": "R07.9",  "category": "pain",          "aliases": ["chest hurts", "pain in chest", "chest pressure", "chest tightness", "tightness in chest", "heart pain"]},
    {"term": "abdominal pain",     "icd10": "R10.9",  "category": "pain",          "aliases": ["stomach pain", "tummy hurts", "belly pain", "stomach ache", "stomach hurts", "gut pain", "abdominal cramps", "tummy ache", "belly ache", "side pain"]},
    {"term": "back pain",          "icd10": "M54.9",  "category": "pain",          "aliases": ["back hurts", "lower back pain", "upper back", "spine pain", "backache"]},
    {"term": "joint pain",         "icd10": "M25.50", "category": "pain",          "aliases": ["joints hurt", "knee pain", "hip pain", "elbow pain", "wrist pain", "ankle pain", "joint ache", "arthritis pain", "stiff joints"]},
    {"term": "muscle pain",        "icd10": "M79.10", "category": "pain",          "aliases": ["muscles hurt", "sore muscles", "body aches", "aching all over", "myalgia", "muscle cramps"]},
    {"term": "neck pain",          "icd10": "M54.2",  "category": "pain",          "aliases": ["neck hurts", "stiff neck", "neck stiffness", "neck ache"]},
    {"term": "pelvic pain",        "icd10": "R10.2",  "category": "pain",          "aliases": ["pain in pelvis", "groin pain", "lower abdomen pain"]},
    {"term": "eye pain",           "icd10": "H57.10", "category": "pain",          "aliases": ["eyes hurt", "eye ache", "pain behind eyes"]},
    {"term": "ear pain",           "icd10": "H92.09", "category": "pain",          "aliases": ["ear hurts", "earache", "ear ache"]},
    {"term": "throat pain",        "icd10": "R07.0",  "category": "pain",          "aliases": ["sore throat", "throat hurts", "painful swallowing", "swollen throat"]},
    {"term": "toothache",          "icd10": "K08.89", "category": "pain",          "aliases": ["tooth hurts", "tooth pain", "dental pain", "jaw pain"]},

    # ── Respiratory ────────────────────────────────────────────────────────────
    {"term": "cough",              "icd10": "R05.9",  "category": "respiratory",   "aliases": ["coughing", "dry cough", "wet cough", "persistent cough", "hacking cough", "coughing up"]},
    {"term": "shortness of breath","icd10": "R06.00", "category": "respiratory",   "aliases": ["cant breathe", "hard to breathe", "breathing difficulty", "out of breath", "breathless", "dyspnea", "gasping", "winded"]},
    {"term": "wheezing",           "icd10": "R06.2",  "category": "respiratory",   "aliases": ["wheeze", "whistling breath", "breathing sounds"]},
    {"term": "congestion",         "icd10": "R09.81", "category": "respiratory",   "aliases": ["stuffy nose", "blocked nose", "nasal congestion", "stuffed up", "congested"]},
    {"term": "runny nose",         "icd10": "R09.89", "category": "respiratory",   "aliases": ["nose running", "rhinorrhea", "dripping nose", "sniffles"]},
    {"term": "sneezing",           "icd10": "R06.7",  "category": "respiratory",   "aliases": ["sneeze", "keep sneezing"]},
    {"term": "sputum production",  "icd10": "R09.3",  "category": "respiratory",   "aliases": ["coughing up mucus", "phlegm", "mucus", "spitting up stuff"]},
    {"term": "chest tightness",    "icd10": "R07.89", "category": "respiratory",   "aliases": ["tight chest", "chest feels tight", "constricted chest"]},

    # ── Digestive ──────────────────────────────────────────────────────────────
    {"term": "nausea",             "icd10": "R11.0",  "category": "digestive",     "aliases": ["nauseous", "feel sick", "queasy", "going to throw up", "stomach turning"]},
    {"term": "vomiting",           "icd10": "R11.10", "category": "digestive",     "aliases": ["throwing up", "puking", "vomit", "being sick"]},
    {"term": "diarrhea",           "icd10": "R19.7",  "category": "digestive",     "aliases": ["loose stools", "watery stools", "runny tummy", "frequent bowel", "runs"]},
    {"term": "constipation",       "icd10": "K59.00", "category": "digestive",     "aliases": ["cant poop", "hard stools", "blocked", "not going to bathroom", "irregular bowels"]},
    {"term": "bloating",           "icd10": "R14.0",  "category": "digestive",     "aliases": ["bloated", "swollen belly", "belly swelling", "gassy", "gas", "flatulence", "distended"]},
    {"term": "heartburn",          "icd10": "R12",    "category": "digestive",     "aliases": ["acid reflux", "reflux", "burning in chest after eating", "indigestion", "gerd"]},
    {"term": "difficulty swallowing","icd10": "R13.10","category": "digestive",     "aliases": ["hard to swallow", "cant swallow", "food stuck", "dysphagia"]},
    {"term": "blood in stool",     "icd10": "K92.1",  "category": "digestive",     "aliases": ["bloody stool", "rectal bleeding", "blood when wiping"]},

    # ── Neurological ───────────────────────────────────────────────────────────
    {"term": "dizziness",          "icd10": "R42",    "category": "neurological",  "aliases": ["dizzy", "lightheaded", "light headed", "room spinning", "vertigo", "unsteady", "off balance"]},
    {"term": "numbness",           "icd10": "R20.0",  "category": "neurological",  "aliases": ["numb", "tingling", "pins and needles", "loss of feeling", "prickling"]},
    {"term": "tremor",             "icd10": "R25.1",  "category": "neurological",  "aliases": ["shaking", "trembling", "hands shaking", "shaky"]},
    {"term": "seizure",            "icd10": "R56.9",  "category": "neurological",  "aliases": ["convulsion", "fit", "epileptic", "blacked out and shook"]},
    {"term": "confusion",          "icd10": "R41.0",  "category": "neurological",  "aliases": ["confused", "disoriented", "brain fog", "foggy", "cant think clearly", "mental fog", "forgetful"]},
    {"term": "memory problems",    "icd10": "R41.3",  "category": "neurological",  "aliases": ["forgetting things", "memory loss", "cant remember", "losing memory"]},
    {"term": "vision changes",     "icd10": "H53.9",  "category": "neurological",  "aliases": ["blurry vision", "seeing spots", "double vision", "cant see well", "vision blurry", "blind spots"]},
    {"term": "hearing loss",       "icd10": "H91.90", "category": "neurological",  "aliases": ["cant hear", "hard of hearing", "ringing in ears", "tinnitus", "ears ringing"]},
    {"term": "speech difficulty",  "icd10": "R47.89", "category": "neurological",  "aliases": ["slurred speech", "cant speak", "trouble talking", "words not coming out"]},
    {"term": "fainting",           "icd10": "R55",    "category": "neurological",  "aliases": ["passed out", "fainted", "blacked out", "syncope", "lost consciousness"]},

    # ── Mood / Mental Health ───────────────────────────────────────────────────
    {"term": "anxiety",            "icd10": "F41.9",  "category": "mood",          "aliases": ["anxious", "worried", "nervous", "panic", "panicking", "on edge", "restless", "cant relax", "fear", "scared"]},
    {"term": "depression",         "icd10": "F32.9",  "category": "mood",          "aliases": ["depressed", "sad", "hopeless", "down", "feeling low", "no motivation", "dont care anymore", "empty", "crying"]},
    {"term": "irritability",       "icd10": "R45.4",  "category": "mood",          "aliases": ["irritable", "angry", "short tempered", "snapping", "agitated", "frustrated"]},
    {"term": "stress",             "icd10": "Z73.3",  "category": "mood",          "aliases": ["stressed", "overwhelmed", "burned out", "burnout", "too much", "under pressure"]},
    {"term": "mood swings",        "icd10": "R45.89", "category": "mood",          "aliases": ["moody", "emotional", "up and down", "unpredictable mood"]},
    {"term": "loss of interest",   "icd10": "R45.89", "category": "mood",          "aliases": ["dont enjoy anything", "lost interest", "nothing is fun", "apathy", "dont care"]},
    {"term": "concentration difficulty","icd10":"R41.840","category": "mood",       "aliases": ["cant concentrate", "cant focus", "distracted", "attention problems", "unfocused"]},

    # ── Skin ───────────────────────────────────────────────────────────────────
    {"term": "rash",               "icd10": "R21",    "category": "dermatological","aliases": ["skin rash", "redness", "red spots", "hives", "bumps on skin", "itchy skin", "breaking out"]},
    {"term": "itching",            "icd10": "L29.9",  "category": "dermatological","aliases": ["itchy", "scratching", "skin itches", "pruritus"]},
    {"term": "swelling",           "icd10": "R60.9",  "category": "dermatological","aliases": ["swollen", "puffiness", "edema", "puffy", "inflamed", "inflammation"]},
    {"term": "bruising",           "icd10": "R23.3",  "category": "dermatological","aliases": ["bruises", "black and blue", "easy bruising"]},
    {"term": "skin discoloration", "icd10": "L81.9",  "category": "dermatological","aliases": ["skin color change", "yellowing", "pale skin", "jaundice", "skin turning yellow"]},

    # ── Cardiovascular ─────────────────────────────────────────────────────────
    {"term": "palpitations",       "icd10": "R00.2",  "category": "cardiovascular","aliases": ["heart racing", "heart pounding", "fast heartbeat", "fluttering", "irregular heartbeat", "skipping beats"]},
    {"term": "high blood pressure","icd10": "I10",    "category": "cardiovascular","aliases": ["hypertension", "blood pressure high", "bp high"]},
    {"term": "low blood pressure", "icd10": "I95.9",  "category": "cardiovascular","aliases": ["hypotension", "blood pressure low", "bp low"]},
    {"term": "leg swelling",       "icd10": "R60.0",  "category": "cardiovascular","aliases": ["swollen legs", "swollen ankles", "feet swelling", "edema in legs"]},

    # ── Urinary ────────────────────────────────────────────────────────────────
    {"term": "frequent urination", "icd10": "R35.0",  "category": "urinary",       "aliases": ["peeing a lot", "urinating often", "going to bathroom a lot", "polyuria"]},
    {"term": "painful urination",  "icd10": "R30.0",  "category": "urinary",       "aliases": ["burns when peeing", "hurts to pee", "dysuria", "burning urination"]},
    {"term": "blood in urine",     "icd10": "R31.9",  "category": "urinary",       "aliases": ["bloody urine", "red urine", "hematuria"]},
]

# ─── Body Part Mappings ────────────────────────────────────────────────────────
BODY_PARTS = {
    "head": "head", "skull": "head", "forehead": "head", "temple": "head",
    "neck": "neck", "throat": "throat",
    "chest": "chest", "breast": "chest", "rib": "chest", "sternum": "chest",
    "stomach": "abdomen", "belly": "abdomen", "tummy": "abdomen", "abdomen": "abdomen", "gut": "abdomen",
    "back": "back", "spine": "back", "lower back": "back", "upper back": "back",
    "arm": "upper extremity", "hand": "upper extremity", "wrist": "upper extremity",
    "finger": "upper extremity", "elbow": "upper extremity", "shoulder": "upper extremity",
    "leg": "lower extremity", "knee": "lower extremity", "ankle": "lower extremity",
    "foot": "lower extremity", "toe": "lower extremity", "hip": "lower extremity", "thigh": "lower extremity",
    "eye": "eye", "eyes": "eye", "ear": "ear", "ears": "ear", "nose": "nose",
    "mouth": "mouth", "jaw": "mouth", "teeth": "mouth", "tooth": "mouth", "tongue": "mouth",
    "skin": "skin", "pelvis": "pelvis", "groin": "pelvis",
}


def _preprocess(text: str) -> str:
    """Lowercase + strip punctuation for matching."""
    return re.sub(r"[^\w\s]", " ", text.lower()).strip()


def _is_negated(clean_text: str, candidates: List[str]) -> bool:
    """Check if any of the matched candidates are preceded by negation words."""
    negation_words = r'\b(no|not|deny|without|doesn\'t|don\'t|never|cannot|can\'t|isn\'t|aren\'t|wasn\'t|weren\'t)\b'
    for candidate in candidates:
        if len(candidate) < 3:
            continue
        # Look for a negation word within 6 words prior to the candidate
        pattern = negation_words + r'\s+(?:\w+\s+){0,6}' + re.escape(candidate)
        if re.search(pattern, clean_text):
            return True
    return False

def _fuzzy_match_term(text: str, term_entry: dict, threshold: int = 80) -> float:
    """Return best fuzzy match score (0-1) for a term against input text."""
    candidates = [term_entry["term"]] + term_entry["aliases"]
    clean = _preprocess(text)
    
    # Advanced NLP: Check for negation FIRST
    if _is_negated(clean, candidates):
        return 0.0
        
    best = 0.0
    text_words = set(clean.split())
    
    for candidate in candidates:
        cand_words = set(candidate.split())
        
        # 1. Exact phrase match with boundaries
        if re.search(r'\b' + re.escape(candidate) + r'\b', clean):
            score = 95 if len(candidate) > 4 else 85
            best = max(best, score / 100.0)
            
        # 2. Token overlap and strict fuzzy matching
        else:
            overlap = len(cand_words.intersection(text_words))
            if overlap > 0 and overlap == len(cand_words):
                best = max(best, 0.8)
            else:
                # token_set_ratio is MUCH safer than partial_ratio against long strings
                ratio = fuzz.token_set_ratio(candidate, clean)
                req_thresh = 95 if len(candidate) <= 5 else threshold
                if ratio >= req_thresh:
                    best = max(best, ratio / 100.0)
    return best


def _detect_body_parts(text: str) -> List[str]:
    """Find body part mentions."""
    clean = _preprocess(text)
    found = []
    for part_alias, canonical in BODY_PARTS.items():
        if part_alias in clean and canonical not in found:
            found.append(canonical)
    return found


def extract_symptoms(text: str) -> Dict[str, Any]:
    """
    Main extraction function.
    Input:  raw user text (e.g. "my tummy hurts really bad and I feel dizzy")
    Output: {
        "symptoms": [ {raw_text, normalized_term, icd10_code, confidence, category} ],
        "body_parts": ["abdomen"],
        "categories_detected": ["pain", "neurological"]
    }
    """
    if not text or not text.strip():
        return {"symptoms": [], "body_parts": [], "categories_detected": []}

    results = []
    seen_terms = set()

    for entry in MEDICAL_TERMS:
        score = _fuzzy_match_term(text, entry)
        if score > 0.0 and entry["term"] not in seen_terms:
            results.append({
                "raw_text": text,
                "normalized_term": entry["term"],
                "icd10_code": entry["icd10"],
                "confidence": round(score, 3),
                "category": entry["category"],
            })
            seen_terms.add(entry["term"])

    # Sort by confidence descending
    results.sort(key=lambda x: x["confidence"], reverse=True)

    body_parts = _detect_body_parts(text)
    categories = list(dict.fromkeys(r["category"] for r in results))

    return {
        "symptoms": results,
        "body_parts": body_parts,
        "categories_detected": categories,
    }


def get_primary_category(text: str) -> str:
    """Return the top detected symptom category, or 'general'."""
    result = extract_symptoms(text)
    cats = result["categories_detected"]
    return cats[0] if cats else "general"


# ── Quick test ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "my tummy hurts really bad",
        "I feel so tired all the time and I can't sleep",
        "IT HURTS SO MUCH I cant breathe",
        "I just feel off, something is not right",
        "headache and dizzy with blurry vision",
        "I've been having chest pain and my heart is racing",
        "feeling anxious and depressed, can't concentrate",
    ]
    for t in tests:
        r = extract_symptoms(t)
        print(f"\n─── Input: {t}")
        for s in r["symptoms"][:5]:
            print(f"  → {s['normalized_term']} ({s['icd10_code']}) conf={s['confidence']}")
        print(f"  Body parts: {r['body_parts']}")
        print(f"  Categories: {r['categories_detected']}")
