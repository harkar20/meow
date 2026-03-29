import { useRef, useState, useCallback } from "react";

const HEDGE_WORDS = ["maybe", "just", "a little", "probably", "might", "sort of", "kind of", "not sure", "i think", "perhaps", "possibly"];

export function useBehavioralCapture() {
  const deletedSegments = useRef([]);
  const keystrokeTimestamps = useRef([]);
  const editCount = useRef(0);
  const lastValue = useRef("");
  const [hedgeCount, setHedgeCount] = useState(0);

  const onKeyDown = useCallback((e) => {
    keystrokeTimestamps.current.push(Date.now());
  }, []);

  const onBeforeInput = useCallback((e) => {
    if (e.inputType === "deleteContentBackward" || e.inputType === "deleteContentForward") {
      const target = e.target;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const val = target.value;
      const deleted = start !== end ? val.slice(start, end) : val.slice(Math.max(0, start - 1), start);
      if (deleted.trim().length > 1) {
        deletedSegments.current.push(deleted);
        editCount.current += 1;
      }
    }
  }, []);

  const onChange = useCallback((e) => {
    const val = e.target.value;
    lastValue.current = val;
    const lower = val.toLowerCase();
    const count = HEDGE_WORDS.filter((w) => lower.includes(w)).length;
    setHedgeCount(count);
  }, []);

  const getMetadata = useCallback(() => {
    const ts = keystrokeTimestamps.current;
    const latencies = ts.slice(1).map((t, i) => t - ts[i]);
    return {
      deleted_segments: [...deletedSegments.current],
      keystroke_timestamps: [...ts],
      typing_latency_ms: latencies,
      edit_count: editCount.current,
      hedge_word_count: hedgeCount,
    };
  }, [hedgeCount]);

  const reset = useCallback(() => {
    deletedSegments.current = [];
    keystrokeTimestamps.current = [];
    editCount.current = 0;
    lastValue.current = "";
    setHedgeCount(0);
  }, []);

  return { onKeyDown, onBeforeInput, onChange, getMetadata, reset, hedgeCount };
}
