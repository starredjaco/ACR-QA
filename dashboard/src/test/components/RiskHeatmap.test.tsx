import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { RiskHeatmap } from "@/components/findings/RiskHeatmap";

function jsonResp(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json" } });
}

const sample = {
  run_id: 1,
  max_high: 2,
  max_total: 3,
  files: [
    {
      file_path: "app/auth.py",
      high: 2,
      medium: 1,
      low: 0,
      total: 3,
      risk_score: 90,
      top_rules: [{ rule_id: "SEC-001", count: 2 }],
    },
    {
      file_path: "app/views.py",
      high: 0,
      medium: 1,
      low: 1,
      total: 2,
      risk_score: 10,
      top_rules: [{ rule_id: "STYLE-001", count: 1 }],
    },
    {
      file_path: "utils/db.py",
      high: 0,
      medium: 0,
      low: 1,
      total: 1,
      risk_score: 5,
      top_rules: [],
    },
  ],
};

describe("RiskHeatmap", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders loading then tree", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp(sample));
    render(<RiskHeatmap runId={1} />);
    expect(screen.getByTestId("heatmap-loading")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("heatmap")).toBeInTheDocument());
  });

  it("auto-expands top folders with HIGH findings", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp(sample));
    render(<RiskHeatmap runId={1} />);
    await waitFor(() => expect(screen.getByTestId("heatmap-row-app")).toBeInTheDocument());
    // auth.py should be visible because app/ is auto-expanded
    expect(screen.getByTestId("heatmap-row-app/auth.py")).toBeInTheDocument();
  });

  it("renders HIGH badge on rows with high findings", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp(sample));
    render(<RiskHeatmap runId={1} />);
    await waitFor(() => expect(screen.getByTestId("heatmap-row-app/auth.py")).toBeInTheDocument());
    const authRow = screen.getByTestId("heatmap-row-app/auth.py");
    expect(authRow.textContent).toContain("2H");
  });

  it("collapses and expands folder on click", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp(sample));
    render(<RiskHeatmap runId={1} />);
    await waitFor(() => expect(screen.getByTestId("heatmap-row-app/auth.py")).toBeInTheDocument());
    const appRow = screen.getByTestId("heatmap-row-app");
    fireEvent.click(appRow);
    // After click on an already-expanded folder, it collapses
    await waitFor(() =>
      expect(screen.queryByTestId("heatmap-row-app/auth.py")).not.toBeInTheDocument(),
    );
  });

  it("invokes onPathSelect when a row is clicked", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp(sample));
    const onSel = vi.fn();
    render(<RiskHeatmap runId={1} onPathSelect={onSel} />);
    await waitFor(() => expect(screen.getByTestId("heatmap-row-app/auth.py")).toBeInTheDocument());
    fireEvent.click(screen.getByTestId("heatmap-row-app/auth.py"));
    expect(onSel).toHaveBeenCalledWith("app/auth.py");
  });

  it("renders empty state when files list empty", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      jsonResp({ run_id: 1, files: [], max_high: 0, max_total: 0 }),
    );
    render(<RiskHeatmap runId={1} />);
    await waitFor(() => expect(screen.getByTestId("heatmap-empty")).toBeInTheDocument());
  });

  it("renders error on fetch failure", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp({}, 500));
    render(<RiskHeatmap runId={1} />);
    await waitFor(() => expect(screen.getByTestId("heatmap-error")).toBeInTheDocument());
  });

  it("colors high-risk rows redder than low-risk", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(jsonResp(sample));
    render(<RiskHeatmap runId={1} />);
    await waitFor(() => expect(screen.getByTestId("heatmap-row-app/auth.py")).toBeInTheDocument());
    const auth = screen.getByTestId("heatmap-row-app/auth.py");
    const views = screen.getByTestId("heatmap-row-app/views.py");
    expect(Number(auth.getAttribute("data-risk"))).toBeGreaterThan(
      Number(views.getAttribute("data-risk")),
    );
  });
});
