import { useEffect, useRef, useState } from "react";
import { authHeader } from "./auth";

export interface SseEvent {
  type: "progress" | "complete" | "error";
  message: string;
  run_id?: number;
  percent?: number;
}

export function useScanProgress(jobId: string | null) {
  const [events, setEvents] = useState<SseEvent[]>([]);
  const [done, setDone] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!jobId) return;
    const token = authHeader().Authorization ?? "";
    const url = `/v1/scans/${jobId}/events?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const ev: SseEvent = JSON.parse(e.data);
        setEvents((prev) => [...prev, ev]);
        if (ev.type === "complete" || ev.type === "error") {
          setDone(true);
          es.close();
        }
      } catch {
        /* ignore malformed */
      }
    };

    es.onerror = () => {
      setDone(true);
      es.close();
    };

    return () => es.close();
  }, [jobId]);

  return { events, done };
}
