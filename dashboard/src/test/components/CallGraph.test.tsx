import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { CallGraph } from "@/components/findings/CallGraph";

function jsonResp(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json" },
  });
}

const sampleGraph = {
  file_path: "app.py",
  target: "eval_input",
  entry_points: ["run_handler"],
  nodes: [
    { id: "run_handler", name: "run_handler", reachable: true, is_target: false, is_entry: true },
    { id: "helper", name: "helper", reachable: true, is_target: false, is_entry: false },
    { id: "eval_input", name: "eval_input", reachable: true, is_target: true, is_entry: false },
    { id: "get_arg", name: "get_arg", reachable: true, is_target: false, is_entry: false },
    { id: "unused_func", name: "unused_func", reachable: false, is_target: false, is_entry: false },
  ],
  edges: [
    { source: "run_handler", target: "helper" },
    { source: "run_handler", target: "eval_input" },
    { source: "eval_input", target: "get_arg" },
    { source: "unused_func", target: "helper" },
  ],
};

describe("CallGraph", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("shows loading then renders nodes", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp(sampleGraph));
    render(<CallGraph findingId={1} />);
    expect(screen.getByTestId("callgraph-loading")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("callgraph")).toBeInTheDocument());
    expect(screen.getByTestId("node-run_handler")).toBeInTheDocument();
    expect(screen.getByTestId("node-eval_input")).toBeInTheDocument();
    expect(screen.getByTestId("node-unused_func")).toBeInTheDocument();
  });

  it("marks target / entry / dead with data attributes", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp(sampleGraph));
    render(<CallGraph findingId={1} />);
    const target = await screen.findByTestId("node-eval_input");
    expect(target.getAttribute("data-target")).toBe("1");
    expect(screen.getByTestId("node-run_handler").getAttribute("data-entry")).toBe("1");
    expect(screen.getByTestId("node-unused_func").getAttribute("data-reachable")).toBe("0");
  });

  it("renders edges between nodes", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp(sampleGraph));
    render(<CallGraph findingId={1} />);
    await waitFor(() =>
      expect(screen.getByTestId("edge-run_handler-eval_input")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("edge-eval_input-get_arg")).toBeInTheDocument();
  });

  it("invokes onNodeClick when a node is clicked", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp(sampleGraph));
    const click = vi.fn();
    render(<CallGraph findingId={1} onNodeClick={click} />);
    const target = await screen.findByTestId("node-eval_input");
    fireEvent.click(target);
    expect(click).toHaveBeenCalledWith("eval_input");
  });

  it("renders unsupported-language placeholder", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      jsonResp({ file_path: "app.js", target: null, nodes: [], edges: [], unsupported_language: true }),
    );
    render(<CallGraph findingId={2} />);
    await waitFor(() => expect(screen.getByTestId("callgraph-unsupported")).toBeInTheDocument());
  });

  it("renders empty state when no nodes", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      jsonResp({ file_path: "x.py", target: null, nodes: [], edges: [], file_missing: true }),
    );
    render(<CallGraph findingId={3} />);
    await waitFor(() => expect(screen.getByTestId("callgraph-empty")).toBeInTheDocument());
  });

  it("renders error on fetch failure", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp({}, 500));
    render(<CallGraph findingId={4} />);
    await waitFor(() => expect(screen.getByTestId("callgraph-error")).toBeInTheDocument());
  });
});
