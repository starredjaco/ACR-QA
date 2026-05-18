/**
 * AI Chat Sidebar for a finding (v5.0.0 Phase A.1).
 *
 * Streams assistant replies via SSE from POST /v1/findings/{id}/chat.
 * Persists the conversation server-side; lazy-loads history on mount.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { authHeader } from "@/lib/auth";

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  preset: string | null;
  content: string;
  model_name?: string | null;
  latency_ms?: number | null;
  created_at: string;
}

interface Preset {
  key: string;
  label: string;
  prompt: string;
}

interface Props {
  findingId: number;
  className?: string;
  /** Optional: pass an array of presets if already fetched (avoids extra request). */
  presets?: Preset[];
}

const STATIC_PRESETS: Preset[] = [
  { key: "explain", label: "Explain", prompt: "" },
  { key: "exploit", label: "Show Exploit", prompt: "" },
  { key: "pr_comment", label: "Draft PR Comment", prompt: "" },
  { key: "real_in_context", label: "Real In My Context?", prompt: "" },
];

export function ChatSidebar({ findingId, className, presets }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [pendingText, setPendingText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [presetCatalog, setPresetCatalog] = useState<Preset[]>(presets ?? STATIC_PRESETS);

  const abortRef = useRef<AbortController | null>(null);

  // ── Load history + presets ──────────────────────────────────────────────
  useEffect(() => {
    let alive = true;
    fetch(`/v1/findings/${findingId}/chat`, { headers: authHeader() })
      .then((r) => (r.ok ? r.json() : { messages: [] }))
      .then((d) => {
        if (alive) setMessages(d.messages ?? []);
      })
      .catch(() => undefined);
    if (!presets) {
      fetch(`/v1/findings/chat/presets`, { headers: authHeader() })
        .then((r) => (r.ok ? r.json() : null))
        .then((d) => {
          if (alive && Array.isArray(d)) setPresetCatalog(d);
        })
        .catch(() => undefined);
    }
    return () => {
      alive = false;
      abortRef.current?.abort();
    };
  }, [findingId, presets]);

  // ── Send (or run preset) ────────────────────────────────────────────────
  const send = useCallback(
    async (body: { preset?: string; content?: string }) => {
      if (streaming) return;
      setError(null);
      setStreaming(true);
      setPendingText("");

      // Optimistically append the user turn
      const userContent =
        body.preset
          ? presetCatalog.find((p) => p.key === body.preset)?.label ?? body.preset
          : (body.content ?? "");
      const tempUserMsg: ChatMessage = {
        id: -Date.now(),
        role: "user",
        preset: body.preset ?? null,
        content: userContent,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);
      setDraft("");

      const ctrl = new AbortController();
      abortRef.current = ctrl;

      try {
        const resp = await fetch(`/v1/findings/${findingId}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeader() },
          body: JSON.stringify(body),
          signal: ctrl.signal,
        });
        if (!resp.ok || !resp.body) {
          throw new Error(`HTTP ${resp.status}`);
        }
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        let assistantText = "";
        let doneMessageId: number | null = null;

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const lines = buf.split("\n\n");
          buf = lines.pop() ?? "";
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data:")) continue;
            try {
              const payload = JSON.parse(trimmed.slice(5).trim());
              if (payload.event === "delta" && typeof payload.text === "string") {
                assistantText += payload.text;
                setPendingText(assistantText);
              } else if (payload.event === "done") {
                doneMessageId = payload.message_id ?? null;
              }
            } catch {
              /* ignore */
            }
          }
        }

        const finalMsg: ChatMessage = {
          id: doneMessageId ?? -(Date.now() + 1),
          role: "assistant",
          preset: body.preset ?? null,
          content: assistantText,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, finalMsg]);
        setPendingText("");
      } catch (err) {
        const msg = err instanceof Error ? err.message : "stream failed";
        setError(msg);
      } finally {
        setStreaming(false);
        abortRef.current = null;
      }
    },
    [findingId, streaming, presetCatalog],
  );

  const handleClear = useCallback(async () => {
    abortRef.current?.abort();
    setMessages([]);
    setPendingText("");
    setError(null);
    await fetch(`/v1/findings/${findingId}/chat`, {
      method: "DELETE",
      headers: authHeader(),
    }).catch(() => undefined);
  }, [findingId]);

  return (
    <aside
      data-testid="chat-sidebar"
      className={`flex flex-col gap-3 rounded-lg border bg-card p-4 ${className ?? ""}`}
    >
      <header className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">AI Chat</h3>
        <button
          type="button"
          className="text-xs text-muted-foreground hover:text-foreground"
          onClick={handleClear}
          disabled={streaming || messages.length === 0}
          aria-label="Clear chat"
        >
          Clear
        </button>
      </header>

      <div className="flex flex-wrap gap-2">
        {presetCatalog.map((p) => (
          <button
            key={p.key}
            type="button"
            data-testid={`preset-${p.key}`}
            className="rounded-md border px-2 py-1 text-xs hover:bg-muted disabled:opacity-50"
            disabled={streaming}
            onClick={() => send({ preset: p.key })}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div
        data-testid="chat-thread"
        className="flex max-h-[460px] flex-col gap-3 overflow-y-auto rounded-md border bg-muted/20 p-3"
        aria-live="polite"
      >
        {messages.length === 0 && !pendingText && (
          <p className="text-xs text-muted-foreground">
            Ask anything about this finding, or pick a preset above.
          </p>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            data-role={m.role}
            className={
              m.role === "user"
                ? "self-end max-w-[85%] rounded-md bg-primary/10 px-3 py-2 text-sm"
                : "self-start max-w-[95%] rounded-md bg-background px-3 py-2 text-sm whitespace-pre-wrap"
            }
          >
            {m.content}
          </div>
        ))}
        {pendingText && (
          <div
            data-testid="streaming-bubble"
            className="self-start max-w-[95%] rounded-md bg-background px-3 py-2 text-sm whitespace-pre-wrap"
          >
            {pendingText}
            <span className="ml-1 animate-pulse text-muted-foreground">▍</span>
          </div>
        )}
      </div>

      {error && (
        <div role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {error}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          const text = draft.trim();
          if (!text || streaming) return;
          void send({ content: text });
        }}
        className="flex gap-2"
      >
        <input
          type="text"
          aria-label="Chat message"
          placeholder="Ask about this finding…"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          disabled={streaming}
          className="flex-1 rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <button
          type="submit"
          disabled={streaming || draft.trim().length === 0}
          className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {streaming ? "…" : "Send"}
        </button>
      </form>
    </aside>
  );
}
