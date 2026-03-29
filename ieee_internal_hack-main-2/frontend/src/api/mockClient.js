// Demo mode - works without backend for presentations
// Replace api/client.js with this version for live demo

import { useAuthStore } from "../store/authStore";

// Mock delay to simulate network
const delay = (ms) => new Promise(r => setTimeout(r, ms));

const mock = {
  async post(url, data) {
    await delay(600);
    
    // Auth endpoints
    if (url.includes("/auth/login") || url.includes("/auth/register") || url.includes("/auth/google")) {
      const user = {
        id: "demo-user-001",
        email: data?.email || "demo@meowmeow.ai",
        full_name: data?.full_name || "Demo Patient",
        age: data?.age || 28,
        sex: data?.sex || "prefer not to say",
        photo_url: null,
        created_at: new Date().toISOString(),
      };
      return { data: { access_token: "demo-token-xyz", user } };
    }
    
    // Start session
    if (url.includes("/session/start")) {
      return {
        data: {
          session_id: `session-${Date.now()}`,
          first_question: "How would you describe how you have been feeling overall lately?",
          question_category: "general",
        },
      };
    }

    // Submit answer
    if (url.includes("/session/answer")) {
      const questions = [
        { text: "Where exactly do you feel discomfort — can you point to a specific area of your body?", category: "location" },
        { text: "When did this first start, and has it been constant or coming and going?", category: "onset" },
        { text: "On a scale from 1 to 10, how much is this affecting your daily activities right now?", category: "severity" },
        { text: "Have you noticed anything specific that makes it better or worse — rest, movement, food, or time of day?", category: "modifiers" },
      ];
      const depth = data?.behavioral_metadata ? 1 : 0;
      const stored = JSON.parse(sessionStorage.getItem("demo_depth") || "0");
      const nextDepth = stored + 1;
      sessionStorage.setItem("demo_depth", nextDepth);
      const complete = nextDepth >= 5;
      return {
        data: {
          next_question: complete ? null : questions[Math.min(nextDepth - 1, questions.length - 1)].text,
          next_question_category: complete ? null : questions[Math.min(nextDepth - 1, questions.length - 1)].category,
          interview_complete: complete,
          current_depth: nextDepth,
          progress_pct: (nextDepth / 5) * 100,
        },
      };
    }

    // Population report
    if (url.includes("/population/report")) {
      return { data: { status: "ok" } };
    }

    throw new Error(`Unknown POST: ${url}`);
  },

  async get(url) {
    await delay(400);

    // Get result
    if (url.includes("/session/result/")) {
      sessionStorage.setItem("demo_depth", "0");
      return {
        data: {
          session_id: url.split("/").pop(),
          risk_tier: "medium",
          risk_score: 0.67,
          top_conditions: [
            { name: "Tension-Type Headache", confidence: 0.72, icd10: "G44.2" },
            { name: "Anxiety Disorder", confidence: 0.58, icd10: "F41.1" },
            { name: "Fatigue Syndrome", confidence: 0.44, icd10: "R53.83" },
          ],
          reasoning_chain: [
            "Reported diffuse discomfort with gradual onset suggests non-acute etiology.",
            "High intensity signals detected in typed responses (uppercase emphasis, repeated phrases).",
            "Deletion patterns indicate minimization of severity — clinical signals suggest higher impact than reported.",
            "Symptom cluster consistent with tension-type headache with anxiety comorbidity (67% posterior probability).",
            "No acute red flags detected. Recommend primary care consultation within 48–72 hours.",
          ],
          behavioral_flags: [
            "Typing hesitation > 2000ms detected on severity question (hesitation event)",
            "Hedge language detected: 'just', 'maybe', 'a little' — possible minimization",
            "Deleted text on severity question contained pain descriptor ('really bad')",
          ],
          recommended_action: "Schedule a consultation with your primary care physician within 48–72 hours. If symptoms worsen significantly or you experience sudden severe headache, seek urgent care immediately.",
          trajectory_label: null,
          trajectory_score: null,
        },
      };
    }

    // History
    if (url.includes("/session/history")) {
      return {
        data: [
          {
            session_id: "session-demo-001",
            created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
            risk_tier: "medium",
            top_condition: "Tension-Type Headache",
            status: "completed",
          },
          {
            session_id: "session-demo-002",
            created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
            risk_tier: "low",
            top_condition: "Seasonal Allergies",
            status: "completed",
          },
        ],
      };
    }

    // Population summary
    if (url.includes("/population/summary")) {
      return {
        data: [
          { city: "Mumbai", region: "Maharashtra", symptom_category: "fatigue", date: new Date().toISOString() },
          { city: "Delhi", region: "Delhi", symptom_category: "respiratory", date: new Date().toISOString() },
          { city: "Bangalore", region: "Karnataka", symptom_category: "pain", date: new Date().toISOString() },
          { city: "Mumbai", region: "Maharashtra", symptom_category: "pain", date: new Date().toISOString() },
          { city: "Chennai", region: "Tamil Nadu", symptom_category: "digestive", date: new Date().toISOString() },
          { city: "Hyderabad", region: "Telangana", symptom_category: "neurological", date: new Date().toISOString() },
          { city: "Delhi", region: "Delhi", symptom_category: "mood", date: new Date().toISOString() },
          { city: "Bangalore", region: "Karnataka", symptom_category: "fatigue", date: new Date().toISOString() },
          { city: "Pune", region: "Maharashtra", symptom_category: "respiratory", date: new Date().toISOString() },
          { city: "Kolkata", region: "West Bengal", symptom_category: "fatigue", date: new Date().toISOString() },
          { city: "Delhi", region: "Delhi", symptom_category: "respiratory", date: new Date().toISOString() },
          { city: "Mumbai", region: "Maharashtra", symptom_category: "neurological", date: new Date().toISOString() },
        ],
      };
    }

    // Auth me
    if (url.includes("/auth/me")) {
      return {
        data: {
          id: "demo-user-001",
          email: "demo@meowmeow.ai",
          full_name: "Demo Patient",
          age: 28, sex: null, photo_url: null,
          created_at: new Date().toISOString(),
        },
      };
    }

    throw new Error(`Unknown GET: ${url}`);
  },

  async patch(url, data) {
    await delay(300);
    return { data: { ...data, id: "demo-user-001", email: "demo@meowmeow.ai", created_at: new Date().toISOString() } };
  }
};

export default mock;
