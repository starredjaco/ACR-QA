import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ChatSidebar } from "@/components/findings/ChatSidebar";

// ── Helpers ──────────────────────────────────────────────────────────────────

function sseChunk(parts: object[]): Uint8Array {
  const enc = new TextEncoder();
  const body = parts.map((p) => `data: ${JSON.stringify(p)}\n\n`).join("");
  return enc.encode(body);
}

function streamedBodyResponse(parts: object[]): Response {
  // happy-dom's Response does not accept a ReadableStream as body, so we
  // hand-roll a Response-like object with the fields the component touches.
  const chunk = sseChunk(parts);
  let yielded = false;
  const reader = {
    read: () =>
      Promise.resolve(
        yielded ? { value: undefined, done: true } : ((yielded = true), { value: chunk, done: false }),
      ),
  } as unknown as ReadableStreamDefaultReader<Uint8Array>;
  return {
    ok: true,
    status: 200,
    body: { getReader: () => reader } as unknown as ReadableStream<Uint8Array>,
  } as unknown as Response;
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  });
}

// ── Fixture ──────────────────────────────────────────────────────────────────

const presets = [
  { key: "explain", label: "Explain", prompt: "Explain prompt." },
  { key: "exploit", label: "Show Exploit", prompt: "Exploit prompt." },
  { key: "pr_comment", label: "Draft PR Comment", prompt: "PR prompt." },
  { key: "real_in_context", label: "Real In My Context?", prompt: "Real prompt." },
];

describe("ChatSidebar", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders four preset buttons", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResponse({ messages: [] }));
    render(<ChatSidebar findingId={1} presets={presets} />);
    expect(screen.getByTestId("preset-explain")).toBeInTheDocument();
    expect(screen.getByTestId("preset-exploit")).toBeInTheDocument();
    expect(screen.getByTestId("preset-pr_comment")).toBeInTheDocument();
    expect(screen.getByTestId("preset-real_in_context")).toBeInTheDocument();
  });

  it("loads chat history on mount", async () => {
    const history = {
      finding_id: 1,
      messages: [
        { id: 1, role: "user", preset: null, content: "Hi", created_at: "t" },
        { id: 2, role: "assistant", preset: null, content: "Hello!", created_at: "t" },
      ],
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResponse(history));
    render(<ChatSidebar findingId={1} presets={presets} />);
    await waitFor(() => expect(screen.getByText("Hi")).toBeInTheDocument());
    expect(screen.getByText("Hello!")).toBeInTheDocument();
  });

  it("renders empty-state hint when no history", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResponse({ messages: [] }));
    render(<ChatSidebar findingId={1} presets={presets} />);
    await waitFor(() =>
      expect(screen.getByText(/ask anything about this finding/i)).toBeInTheDocument(),
    );
  });

  it("disables send button when input empty", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResponse({ messages: [] }));
    render(<ChatSidebar findingId={1} presets={presets} />);
    const btn = screen.getByRole("button", { name: /send/i });
    expect(btn).toBeDisabled();
  });

  it("optimistically renders user message and POSTs to API", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch") as unknown as ReturnType<typeof vi.fn>;
    fetchSpy
      .mockResolvedValueOnce(jsonResponse({ messages: [] }))
      .mockResolvedValueOnce(streamedBodyResponse([{ event: "done", message_id: 1 }]));

    render(<ChatSidebar findingId={1} presets={presets} />);
    const input = screen.getByLabelText(/chat message/i);
    fireEvent.change(input, { target: { value: "hi there" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => expect(screen.getByText("hi there")).toBeInTheDocument());

    const postCall = fetchSpy.mock.calls.find((c) => c[1] && (c[1] as RequestInit).method === "POST");
    expect(postCall).toBeTruthy();
    const body = JSON.parse((postCall![1] as RequestInit).body as string);
    expect(body.content).toBe("hi there");
    expect(postCall![0]).toBe("/v1/findings/1/chat");
  });

  it("fires preset POST with preset key in body", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch") as unknown as ReturnType<typeof vi.fn>;
    fetchSpy
      .mockResolvedValueOnce(jsonResponse({ messages: [] }))
      .mockResolvedValueOnce(streamedBodyResponse([{ event: "done", message_id: 9 }]));

    render(<ChatSidebar findingId={42} presets={presets} />);
    fireEvent.click(screen.getByTestId("preset-explain"));

    await waitFor(() => {
      const postCall = fetchSpy.mock.calls.find((c) => c[1] && (c[1] as RequestInit).method === "POST");
      expect(postCall).toBeTruthy();
    });
    const postCall = fetchSpy.mock.calls.find((c) => c[1] && (c[1] as RequestInit).method === "POST");
    const body = JSON.parse((postCall![1] as RequestInit).body as string);
    expect(body.preset).toBe("explain");
    expect(postCall![0]).toBe("/v1/findings/42/chat");
  });

  it("renders error bubble on fetch failure", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch") as unknown as ReturnType<typeof vi.fn>;
    fetchSpy
      .mockResolvedValueOnce(jsonResponse({ messages: [] }))
      .mockResolvedValueOnce(jsonResponse({ detail: "nope" }, 500));

    render(<ChatSidebar findingId={1} presets={presets} />);
    fireEvent.change(screen.getByLabelText(/chat message/i), { target: { value: "boom" } });
    fireEvent.click(screen.getByRole("button", { name: /send/i }));

    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });

  it("clear button DELETEs and empties thread", async () => {
    const history = {
      finding_id: 1,
      messages: [{ id: 1, role: "user", preset: null, content: "x", created_at: "t" }],
    };
    const fetchSpy = vi.spyOn(globalThis, "fetch") as unknown as ReturnType<typeof vi.fn>;
    fetchSpy
      .mockResolvedValueOnce(jsonResponse(history))
      .mockResolvedValueOnce(jsonResponse({ finding_id: 1, deleted: 1 }));

    render(<ChatSidebar findingId={1} presets={presets} />);
    await waitFor(() => expect(screen.getByText("x")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /clear chat/i }));
    await waitFor(() => expect(screen.queryByText("x")).not.toBeInTheDocument());
    const deleteCall = fetchSpy.mock.calls.find((c) => c[1] && (c[1] as RequestInit).method === "DELETE");
    expect(deleteCall).toBeTruthy();
  });

  it("fetches presets when not pre-supplied", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch") as unknown as ReturnType<typeof vi.fn>;
    fetchSpy
      .mockResolvedValueOnce(jsonResponse({ messages: [] }))
      .mockResolvedValueOnce(jsonResponse(presets));

    render(<ChatSidebar findingId={1} />);
    await waitFor(() => expect(screen.getByTestId("preset-explain")).toBeInTheDocument());
    const presetCall = fetchSpy.mock.calls.find((c) => String(c[0]).includes("/chat/presets"));
    expect(presetCall).toBeTruthy();
  });
});
