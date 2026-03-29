import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { sessionApi } from "../api/endpoints";
import { useBehavioralCapture } from "../hooks/useBehavioralCapture";
import { Mic, MicOff, Send, Volume2, VolumeX, Cat } from "lucide-react";

const TTS_RATE = 0.88;

function speakText(text, enabled) {
  if (!enabled || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.rate = TTS_RATE;
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find((v) => v.lang.startsWith("en") && v.name.toLowerCase().includes("female"))
    || voices.find((v) => v.lang === "en-GB")
    || voices.find((v) => v.lang.startsWith("en"));
  if (preferred) utt.voice = preferred;
  window.speechSynthesis.speak(utt);
}

export default function InterviewPage() {
  const navigate = useNavigate();
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [currentCategory, setCurrentCategory] = useState("general");
  const [answer, setAnswer] = useState("");
  const [progress, setProgress] = useState(0);
  const [depth, setDepth] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState("");
  const [questionVisible, setQuestionVisible] = useState(true);
  const [currentOptions, setCurrentOptions] = useState(null);

  const behavCapture = useBehavioralCapture();
  const recognitionRef = useRef(null);
  const textareaRef = useRef(null);

  // Start session on mount
  useEffect(() => {
    (async () => {
      try {
        const res = await sessionApi.startSession();
        setSessionId(res.data.session_id);
        setCurrentQuestion(res.data.first_question);
        setCurrentCategory(res.data.question_category);
        setTimeout(() => {
          speakText(res.data.first_question, ttsEnabled);
        }, 600);
      } catch (e) {
        setError("Could not connect to server. Please ensure the backend is running.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // TTS re-speak on question change
  const prevQuestion = useRef("");
  useEffect(() => {
    if (currentQuestion && currentQuestion !== prevQuestion.current) {
      prevQuestion.current = currentQuestion;
      setTimeout(() => speakText(currentQuestion, ttsEnabled), 700);
    }
  }, [currentQuestion, ttsEnabled]);

  const handleSubmit = useCallback(async () => {
    if (!answer.trim() || answer.trim().length < 3 || submitting) return;
    setSubmitting(true);
    setError("");

    try {
      const meta = behavCapture.getMetadata();
      const res = await sessionApi.submitAnswer({
        session_id: sessionId,
        question_text: currentQuestion,
        question_category: currentCategory,
        answer_text: answer.trim(),
        behavioral_metadata: meta,
      });

      setProgress(res.data.progress_pct);
      setDepth(res.data.current_depth);
      behavCapture.reset();

      if (res.data.interview_complete) {
        navigate(`/result/${sessionId}`);
        return;
      }

      // Animate question transition
      setQuestionVisible(false);
      setTimeout(() => {
        setCurrentQuestion(res.data.next_question);
        setCurrentCategory(res.data.next_question_category);
        setCurrentOptions(res.data.options || null);
        setAnswer("");
        setTranscript("");
        setQuestionVisible(true);
        textareaRef.current?.focus();
      }, 400);
    } catch (e) {
      setError("Failed to submit answer. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }, [answer, submitting, sessionId, currentQuestion, currentCategory, behavCapture, navigate]);

  // Keyboard shortcut: Ctrl+Enter to submit
  const handleKeyDown = useCallback((e) => {
    behavCapture.onKeyDown(e);
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") handleSubmit();
  }, [behavCapture, handleSubmit]);

  // Speech recognition
  const toggleListening = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { setError("Speech recognition not supported in this browser."); return; }

    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const rec = new SR();
    recognitionRef.current = rec;
    rec.continuous = false;
    rec.interimResults = true;
    rec.lang = "en-US";

    rec.onresult = (e) => {
      const t = Array.from(e.results).map((r) => r[0].transcript).join("");
      setTranscript(t);
      if (e.results[e.results.length - 1].isFinal) {
        setAnswer((prev) => (prev ? prev + " " + t : t).trim());
        setTranscript("");
        setListening(false);
      }
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    rec.start();
    setListening(true);
  };

  const categoryLabel = {
    general: "General Wellbeing", location: "Location", onset: "Onset & Duration",
    severity: "Severity", modifiers: "Modifying Factors",
    fatigue: "Fatigue", pain: "Pain", respiratory: "Respiratory",
    digestive: "Digestive", neurological: "Neurological", mood: "Mood"
  }[currentCategory] || currentCategory;

  if (loading) {
    return (
      <div className="page-center" style={{ flexDirection: "column", gap: 16 }}>
        <div className="spinner spinner-lg" />
        <p style={{ color: "var(--text-secondary)" }}>Preparing your clinical interview…</p>
      </div>
    );
  }

  return (
    <div className="page-center" style={{ alignItems: "stretch", padding: "1rem" }}>
      <div style={{ width: "100%", maxWidth: 700, margin: "0 auto", display: "flex", flexDirection: "column", gap: "1.5rem" }}>

        {/* Progress */}
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Cat size={16} color="var(--text-primary)" />
              <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: 500 }}>Clinical Interview</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Question {depth + 1}</span>
              <button
                onClick={() => { setTtsEnabled(!ttsEnabled); window.speechSynthesis?.cancel(); }}
                className="btn btn-secondary btn-sm btn-icon"
                title={ttsEnabled ? "Mute voice" : "Enable voice"}
              >
                {ttsEnabled ? <Volume2 size={14} /> : <VolumeX size={14} />}
              </button>
            </div>
          </div>
          <div className="progress-bar-track">
            <motion.div className="progress-bar-fill" animate={{ width: `${progress}%` }} />
          </div>
        </div>

        {/* Category badge */}
        <div style={{ display: "flex", justifyContent: "center" }}>
          <span style={{
            display: "inline-flex", alignItems: "center", gap: 6,
            padding: "4px 14px", borderRadius: "100px",
            background: "var(--bg-card)", border: "1px solid var(--border-color)",
            fontSize: "0.75rem", fontWeight: 600, color: "var(--text-primary)",
            letterSpacing: "0.06em", textTransform: "uppercase"
          }}>
            {categoryLabel}
          </span>
        </div>

        {/* Question */}
        <AnimatePresence mode="wait">
          {questionVisible && (
            <motion.div
              key={currentQuestion}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.4 }}
              style={{ textAlign: "center" }}
            >
              <h2 style={{
                fontFamily: "'Plus Jakarta Sans', sans-serif",
                fontSize: "clamp(1.3rem, 3.5vw, 1.85rem)",
                fontWeight: 700,
                lineHeight: 1.45,
                letterSpacing: "-0.02em",
                color: "var(--text-primary)",
                maxWidth: 600,
                margin: "0 auto",
              }}>
                {currentQuestion}
              </h2>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Answer area */}
        <motion.div
          className="card"
          style={{ padding: "1.5rem" }}
          animate={{ borderColor: answer.length >= 3 ? "var(--text-primary)" : "var(--border-color)" }}
        >
          {transcript && (
            <div style={{
              marginBottom: 10, padding: "8px 12px",
              background: "rgba(6,182,212,0.08)", border: "1px solid rgba(6,182,212,0.2)",
              borderRadius: "var(--radius-sm)", fontSize: "0.85rem", color: "var(--accent-cyan)",
              fontStyle: "italic"
            }}>
              🎙️ {transcript}
            </div>
          )}

          <textarea
            ref={textareaRef}
            className="form-input"
            placeholder="Describe how you're feeling… speak freely, there are no wrong answers."
            value={answer}
            onChange={(e) => { setAnswer(e.target.value); behavCapture.onChange(e); }}
            onKeyDown={handleKeyDown}
            onBeforeInput={behavCapture.onBeforeInput}
            rows={4}
            style={{ resize: "none", marginBottom: "1rem", fontSize: "1rem", lineHeight: 1.6 }}
            autoFocus
          />

          {currentOptions && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: "1rem" }}>
              {currentOptions.map((opt, i) => (
                <button
                  key={i}
                  onClick={() => { setAnswer(opt.label); setTimeout(handleSubmit, 200); }}
                  style={{
                    padding: "8px 16px", borderRadius: "100px", border: "1px solid var(--border-color)",
                    background: answer === opt.label ? "var(--accent-blue)" : "rgba(255,255,255,0.05)",
                    color: answer === opt.label ? "#fff" : "var(--text-primary)",
                    cursor: "pointer", fontWeight: 600, fontSize: "0.85rem", transition: "all 0.2s"
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <motion.button
                className={`btn ${listening ? "btn-danger" : "btn-secondary"} btn-icon`}
                onClick={toggleListening}
                title={listening ? "Stop recording" : "Speak your answer"}
                animate={listening ? { boxShadow: ["0 0 0 0 rgba(239,68,68,0.4)", "0 0 0 8px rgba(239,68,68,0)"] } : {}}
                transition={{ repeat: Infinity, duration: 1 }}
              >
                {listening ? <MicOff size={16} /> : <Mic size={16} />}
              </motion.button>
              {listening && <span style={{ fontSize: "0.8rem", color: "var(--risk-critical)" }}>Listening…</span>}
              {!listening && behavCapture.hedgeCount > 0 && (
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  💭 {behavCapture.hedgeCount} hedge word{behavCapture.hedgeCount > 1 ? "s" : ""} detected
                </span>
              )}
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {depth >= 4 && (
                <button
                  className="btn btn-secondary"
                  disabled={submitting}
                  onClick={() => navigate(`/result/${sessionId}`)}
                  style={{ gap: 8 }}
                >
                  <Cat size={16} /> Generate Diagnosis
                </button>
              )}
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Ctrl+Enter to submit</span>
              <motion.button
                className="btn btn-primary"
                disabled={answer.trim().length < 3 || submitting}
                onClick={handleSubmit}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                style={{ gap: 8 }}
              >
                {submitting ? <><div className="spinner" /> Analyzing…</> : <><Send size={16} /> Submit / Continue</>}
              </motion.button>
            </div>
          </div>
        </motion.div>

        {error && (
          <div style={{ textAlign: "center", color: "#f87171", fontSize: "0.85rem", padding: "8px 16px", background: "rgba(239,68,68,0.08)", borderRadius: "var(--radius-md)", border: "1px solid rgba(239,68,68,0.2)" }}>
            {error}
          </div>
        )}

        <p style={{ textAlign: "center", fontSize: "0.75rem", color: "var(--text-muted)" }}>
          Your responses are analyzed with clinical-grade NLP. Behavioral signals are captured passively to improve accuracy.
        </p>
      </div>
    </div>
  );
}
