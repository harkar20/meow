"""
Meowmeow — ML API Service
FastAPI microservice exposing all ML pipeline endpoints.
Runs on port 8001 — called by the main backend at port 8000.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import traceback

from .nlp_pipeline import extract_symptoms, get_primary_category
from .intensity_analyzer import analyze_intensity
from .interview_graph import get_first_question, get_next_question, TOTAL_QUESTIONS
from .bayesian_engine import run_inference
from .behavioral_processor import process_behavioral_signals
from .trajectory_model import analyze_trajectory
from .speech_processor import process_audio

# ─── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Meowmeow ML Service",
    description="AI/ML microservice for symptom analysis, clinical inference, and risk assessment",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Session State (in-memory for hackathon) ───────────────────────────────────
# Tracks interview branch per session so follow-up questions follow the same branch
_session_state: Dict[str, Dict[str, Any]] = {}


# ─── Pydantic Models ──────────────────────────────────────────────────────────

class ExtractSymptomsRequest(BaseModel):
    text: str

class ExtractSymptomsResponse(BaseModel):
    symptoms: List[Dict[str, Any]]
    body_parts: List[str]
    categories_detected: List[str]


class BehavioralMetadataInput(BaseModel):
    deleted_segments: List[str] = []
    keystroke_timestamps: List[int] = []
    typing_latency_ms: List[int] = []
    edit_count: int = 0
    hedge_word_count: int = 0

class AnalyzeIntensityRequest(BaseModel):
    text: str
    behavioral_metadata: Optional[BehavioralMetadataInput] = None
    audio_base64: Optional[str] = None

class AnalyzeIntensityResponse(BaseModel):
    intensity_score: float
    intensity_level: str
    signals_detected: List[str]
    breakdown: Dict[str, float]


class NextQuestionRequest(BaseModel):
    session_id: str
    answer_text: str
    current_category: str = "general"
    depth: int = 0

class NextQuestionResponse(BaseModel):
    question: Optional[str]
    category: Optional[str]
    depth: int
    branch: str
    total_questions: int
    interview_complete: bool = False
    options: Optional[List[Dict[str, str]]] = None
    symptom_code: Optional[str] = None
    fallback_idx: Optional[int] = None


class AnswerDetail(BaseModel):
    question: str
    answer: str

class InferRequest(BaseModel):
    session_id: str
    combined_text: str
    answers: List[AnswerDetail] = []
    behavioral_metadata: Optional[BehavioralMetadataInput] = None
    audio_base64: Optional[str] = None
    session_history: Optional[List[Dict[str, Any]]] = None

class InferResponse(BaseModel):
    risk_tier: str
    confidence_score: float
    top_conditions: List[Dict[str, Any]]
    reasoning_chain: List[str]
    behavioral_flags: List[str]
    recommended_action: str
    patient_explanation: Optional[str] = None
    doctor_explanation: Optional[str] = None
    trajectory_label: Optional[str] = None
    escalation_score: Optional[float] = None
    intensity: Optional[Dict[str, Any]] = None


class TrajectoryRequest(BaseModel):
    session_history: List[Dict[str, Any]]

class TrajectoryResponse(BaseModel):
    trajectory_label: str
    escalation_score: float
    new_systems_involved: List[str]
    comparison: Dict[str, Any]


class BehavioralRequest(BaseModel):
    answer_text: str
    deleted_segments: List[str] = []
    keystroke_timestamps: List[int] = []
    typing_latency_ms: List[int] = []
    edit_count: int = 0
    hedge_word_count: int = 0
    session_id: str = ""


class AudioProcessRequest(BaseModel):
    audio_base64: str


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "Meowmeow ML Service",
        "version": "1.0.0",
        "endpoints": [
            "/ml/extract-symptoms",
            "/ml/analyze-intensity",
            "/ml/next-question",
            "/ml/infer",
            "/ml/trajectory",
            "/ml/behavioral",
            "/ml/process-audio",
        ],
    }


@app.get("/health")
def health():
    return {"status": "healthy", "service": "ml"}


@app.post("/ml/extract-symptoms", response_model=ExtractSymptomsResponse)
def api_extract_symptoms(req: ExtractSymptomsRequest):
    """Extract medical symptoms from raw text and normalize to ICD-10 codes."""
    try:
        result = extract_symptoms(req.text)
        return ExtractSymptomsResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NLP extraction failed: {str(e)}")


@app.post("/ml/analyze-intensity", response_model=AnalyzeIntensityResponse)
def api_analyze_intensity(req: AnalyzeIntensityRequest):
    """Analyze text intensity from text signals, behavioral metadata, and optional audio."""
    try:
        behav = req.behavioral_metadata.model_dump() if req.behavioral_metadata else None

        # Process audio if provided
        audio_features = None
        if req.audio_base64:
            audio_result = process_audio(req.audio_base64)
            if audio_result.get("features_extracted"):
                audio_features = {
                    "energy_level": audio_result["energy_level"],
                    "speech_rate": audio_result["speech_rate"],
                    "stress_indicators": audio_result.get("stress_indicators", []),
                }

        result = analyze_intensity(req.text, behav, audio_features)
        return AnalyzeIntensityResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intensity analysis failed: {str(e)}")


@app.post("/ml/next-question", response_model=NextQuestionResponse)
def api_next_question(req: NextQuestionRequest):
    """Get the next interview question based on the user's combined answers dynamically."""
    try:
        sid = req.session_id

        # Get or create session state with FULL tracking
        if sid not in _session_state:
            _session_state[sid] = {
                "text": "",
                "depth": 0,
                "asked_symptoms": [],   # ICD-10 codes asked about
                "asked_questions": [],  # Exact question strings shown
                "fallback_idx": 0,      # Pointer into ordered fallback pool
            }

        state = _session_state[sid]
        
        # Append latest answer
        state["text"] += " " + req.answer_text
        state["depth"] = req.depth

        result = get_next_question(
            combined_text=state["text"],
            depth=req.depth,
            asked_symptoms=state["asked_symptoms"],
            asked_questions=state["asked_questions"],
            asked_fallback_idx=state["fallback_idx"],
        )

        # Track EVERYTHING to prevent any repetition
        if result.get("symptom_code"):
            state["asked_symptoms"].append(result["symptom_code"])
        if result.get("question"):
            state["asked_questions"].append(result["question"])
        if result.get("fallback_idx") is not None:
            state["fallback_idx"] = result["fallback_idx"]

        return NextQuestionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Next question failed: {str(e)}")


@app.post("/ml/infer", response_model=InferResponse)
def api_infer(req: InferRequest):
    """Run full clinical inference — the main ML pipeline endpoint."""
    try:
        # Build behavioral metadata dict
        behav = req.behavioral_metadata.model_dump() if req.behavioral_metadata else None

        # Process audio if provided
        audio_features = None
        if req.audio_base64:
            audio_result = process_audio(req.audio_base64)
            if audio_result.get("features_extracted"):
                audio_features = {
                    "energy_level": audio_result["energy_level"],
                    "speech_rate": audio_result["speech_rate"],
                    "stress_indicators": audio_result.get("stress_indicators", []),
                }

        # Run main inference
        answers_list = [{"question": a.question, "answer": a.answer} for a in req.answers]
        inference_result = run_inference(
            text=req.combined_text,
            answers=answers_list,
            behavioral_metadata=behav,
            audio_features=audio_features,
        )

        # Run trajectory if history provided
        trajectory_label = None
        escalation_score = None
        if req.session_history and len(req.session_history) >= 2:
            traj = analyze_trajectory(req.session_history)
            trajectory_label = traj["trajectory_label"]
            escalation_score = traj["escalation_score"]

        return InferResponse(
            risk_tier=inference_result["risk_tier"],
            confidence_score=inference_result["confidence_score"],
            top_conditions=inference_result["top_conditions"],
            reasoning_chain=inference_result["reasoning_chain"],
            behavioral_flags=inference_result["behavioral_flags"],
            recommended_action=inference_result["recommended_action"],
            patient_explanation=inference_result.get("patient_explanation"),
            doctor_explanation=inference_result.get("doctor_explanation"),
            trajectory_label=trajectory_label,
            escalation_score=escalation_score,
            intensity=inference_result.get("intensity"),
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")


@app.post("/ml/trajectory", response_model=TrajectoryResponse)
def api_trajectory(req: TrajectoryRequest):
    """Analyze temporal trajectory across sessions."""
    try:
        result = analyze_trajectory(req.session_history)
        return TrajectoryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trajectory analysis failed: {str(e)}")


@app.post("/ml/behavioral")
def api_behavioral(req: BehavioralRequest):
    """Process behavioral signals from a single answer."""
    try:
        result = process_behavioral_signals(
            answer_text=req.answer_text,
            deleted_segments=req.deleted_segments,
            keystroke_timestamps=req.keystroke_timestamps,
            typing_latency_ms=req.typing_latency_ms,
            edit_count=req.edit_count,
            hedge_word_count=req.hedge_word_count,
            session_id=req.session_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Behavioral processing failed: {str(e)}")


@app.post("/ml/process-audio")
def api_process_audio(req: AudioProcessRequest):
    """Process audio blob and extract features."""
    try:
        result = process_audio(req.audio_base64)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")
