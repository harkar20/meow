from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..models.user import User
from ..models.session import Session as SessionModel, SessionAnswer, PopulationAggregate
from ..schemas.session import (
    SessionStartResponse, AnswerSubmit, AnswerResponse,
    RiskOutput, SessionHistoryItem, PopulationReport
)
from ..auth import get_current_user
from ..services.ml_service import call_ml_service

router = APIRouter(prefix="/session", tags=["session"])

# Default interview tree (used when ML service is unavailable)
DEFAULT_QUESTIONS = [
    {"text": "How would you describe how you have been feeling overall?", "category": "general"},
    {"text": "Where exactly do you feel discomfort — can you point to a specific area of your body?", "category": "location"},
    {"text": "When did this first start, and has it been constant or coming and going?", "category": "onset"},
    {"text": "On a scale from 1 to 10, how much is this affecting your daily life right now?", "category": "severity"},
    {"text": "Have you noticed anything that makes it better or worse?", "category": "modifiers"},
]

@router.post("/start", response_model=SessionStartResponse)
async def start_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = SessionModel(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    first_q = DEFAULT_QUESTIONS[0]
    return SessionStartResponse(
        session_id=session.id,
        first_question=first_q["text"],
        question_category=first_q["category"],
    )

@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    payload: AnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(SessionModel).filter(
        SessionModel.id == payload.session_id,
        SessionModel.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Count existing answers
    answer_count = db.query(SessionAnswer).filter(
        SessionAnswer.session_id == payload.session_id
    ).count()

    # Store answer
    meta = payload.behavioral_metadata.model_dump() if payload.behavioral_metadata else {}
    answer = SessionAnswer(
        session_id=payload.session_id,
        question_text=payload.question_text,
        question_category=payload.question_category,
        answer_text=payload.answer_text,
        behavioral_metadata=meta,
        sequence_number=answer_count,
    )
    db.add(answer)
    db.commit()

    # Try ML service for next question (forward behavioral metadata)
    ml_payload = {
        "session_id": str(payload.session_id),
        "answer_text": payload.answer_text,
        "current_category": payload.question_category,
        "depth": answer_count + 1,
    }
    ml_result = await call_ml_service("next-question", ml_payload)

    # Also run intensity analysis on this answer asynchronously
    intensity_payload = {
        "text": payload.answer_text,
        "behavioral_metadata": meta if meta else None,
    }
    _ = await call_ml_service("analyze-intensity", intensity_payload)

    total_questions = ml_result.get("total_questions", 8)
    next_idx = answer_count + 1
    interview_complete = ml_result.get("interview_complete", next_idx >= total_questions)

    if not interview_complete:
        if ml_result.get("question"):
            next_q = ml_result["question"]
            next_cat = ml_result.get("category", "general")
            next_opt = ml_result.get("options", None)
        else:
            # Fallback
            q = DEFAULT_QUESTIONS[min(next_idx, len(DEFAULT_QUESTIONS) - 1)] if next_idx < len(DEFAULT_QUESTIONS) else DEFAULT_QUESTIONS[-1]
            next_q = q["text"]
            next_cat = q["category"]
            next_opt = None
    else:
        next_q = None
        next_cat = None
        next_opt = None
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        db.commit()

    progress = min(((next_idx) / total_questions) * 100, 100)
    return AnswerResponse(
        next_question=next_q,
        next_question_category=next_cat,
        interview_complete=interview_complete,
        current_depth=next_idx,
        progress_pct=progress,
        options=next_opt,
    )

@router.get("/result/{session_id}", response_model=RiskOutput)
async def get_result(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    answers = db.query(SessionAnswer).filter(
        SessionAnswer.session_id == session_id
    ).order_by(SessionAnswer.sequence_number).all()

    all_text = " ".join([a.answer_text for a in answers])

    # Collect all behavioral metadata from answers
    all_behavioral = {}
    for a in answers:
        if a.behavioral_metadata:
            for key in ["deleted_segments", "typing_latency_ms"]:
                if key in a.behavioral_metadata:
                    all_behavioral.setdefault(key, []).extend(a.behavioral_metadata[key])
            for key in ["edit_count", "hedge_word_count"]:
                if key in a.behavioral_metadata:
                    all_behavioral[key] = all_behavioral.get(key, 0) + a.behavioral_metadata.get(key, 0)

    # Try ML inference with full behavioral context
    ml_result = await call_ml_service("infer", {
        "session_id": str(session_id),
        "combined_text": all_text,
        "answers": [{"question": a.question_text, "answer": a.answer_text} for a in answers],
        "behavioral_metadata": all_behavioral if all_behavioral else None,
    }, timeout=15.0)

    if ml_result.get("risk_tier"):
        risk_tier = ml_result["risk_tier"]
        risk_score = ml_result.get("confidence_score", 0.5)
        top_conditions = ml_result.get("top_conditions", [])
        reasoning = ml_result.get("reasoning_chain", [])
        action = ml_result.get("recommended_action", "Consult a healthcare provider.")
        patient_exp = ml_result.get("patient_explanation", "")
        doctor_exp = ml_result.get("doctor_explanation", "")
        trajectory = ml_result.get("trajectory_label")
        traj_score = ml_result.get("escalation_score")
        beh_flags = ml_result.get("behavioral_flags", [])
    else:
        # Fallback placeholder output
        risk_tier = "medium"
        risk_score = 0.5
        top_conditions = [
            {"name": "Assessment Pending", "confidence": 0.5, "icd10": "Z00.0"},
        ]
        reasoning = ["ML service unavailable — connect the AI module to get full analysis."]
        action = "Please consult a healthcare provider for a full evaluation."
        patient_exp = "The AI module is currently offline. We cannot provide a clinical assessment at this time."
        doctor_exp = "ML infer endpoint unavailable. Differential diagnosis suspended."
        trajectory = None
        traj_score = None
        beh_flags = []

    # Save to session
    session.risk_tier = risk_tier
    session.risk_score = risk_score
    session.top_conditions = top_conditions
    db.commit()

    return RiskOutput(
        session_id=session_id,
        risk_tier=risk_tier,
        risk_score=risk_score,
        top_conditions=top_conditions,
        reasoning_chain=reasoning,
        behavioral_flags=beh_flags,
        recommended_action=action,
        patient_explanation=patient_exp,
        doctor_explanation=doctor_exp,
        trajectory_label=trajectory,
        trajectory_score=traj_score,
    )

@router.get("/history", response_model=List[SessionHistoryItem])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id
    ).order_by(SessionModel.created_at.desc()).limit(20).all()

    result = []
    for s in sessions:
        top = s.top_conditions[0]["name"] if s.top_conditions else None
        result.append(SessionHistoryItem(
            session_id=s.id,
            created_at=s.created_at,
            risk_tier=s.risk_tier,
            top_condition=top,
            status=s.status,
        ))
    return result

@router.post("/population/report")
def population_report(
    payload: PopulationReport,
    db: Session = Depends(get_db)
):
    record = PopulationAggregate(
        region=payload.region,
        city=payload.city,
        symptom_category=payload.symptom_category,
    )
    db.add(record)
    db.commit()
    return {"status": "ok"}

@router.get("/population/summary")
def population_summary(db: Session = Depends(get_db)):
    rows = db.query(PopulationAggregate).order_by(
        PopulationAggregate.date.desc()
    ).limit(200).all()
    return [
        {
            "city": r.city,
            "region": r.region,
            "symptom_category": r.symptom_category,
            "date": r.date.isoformat() if r.date else None,
        }
        for r in rows
    ]
