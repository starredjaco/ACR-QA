import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { RunsResponse, ConfirmedSummary } from "@/lib/api";

// CountUp animates via requestAnimationFrame (non-deterministic under happy-dom).
// Render the raw value synchronously so assertions are stable.
vi.mock("@/components/ui/CountUp", () => ({
  CountUp: ({ value }: { value: number }) => <>{value}</>,
}));

// The overview pulls in chart components that aren't relevant to this test.
vi.mock("@/components/charts/FindingsTrendChart", () => ({
  FindingsTrendChart: () => <div data-testid="trend-chart" />,
}));
vi.mock("@/components/charts/ScanCalendar", () => ({
  ScanCalendar: () => <div data-testid="scan-calendar" />,
}));

const getRuns = vi.fn();
const getConfirmedSummary = vi.fn();

vi.mock("@/lib/api", () => ({
  getRuns: (...args: unknown[]) => getRuns(...args),
  getConfirmedSummary: (...args: unknown[]) => getConfirmedSummary(...args),
}));

import { OverviewPage } from "@/routes/overview";

function makeRun(id: number, high: number, total: number) {
  return {
    id,
    repo_name: `repo-${id}`,
    pr_number: null,
    status: "completed",
    started_at: "2026-06-01T10:00:00Z",
    total_findings: total,
    high_count: high,
    medium_count: 0,
    low_count: total - high,
  };
}

function renderOverview() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <OverviewPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("OverviewPage — Confirmed Tier hero tile", () => {
  beforeEach(() => {
    getRuns.mockReset();
    getConfirmedSummary.mockReset();
  });

  it("shows the REAL server-classified confirmed count, not highCount * 0.25", async () => {
    // 3 runs, total high_count = 40. The old fabrication would render round(40*0.25)=10.
    const runs: RunsResponse = {
      runs: [makeRun(967, 20, 30), makeRun(966, 12, 20), makeRun(965, 8, 15)],
    } as RunsResponse;
    getRuns.mockResolvedValue(runs);

    const summary: ConfirmedSummary = {
      run_id: 967,
      total_findings: 30,
      confirmed_tier_count: 3,
      confirmed_tier_pct: 10.0,
      signals: { exploit: 2, taint: 1 },
      auto_block_safe: false,
      precision_context: {
        confirmed_tier_precision: "96.4%",
        false_positive_tolerance: "<4%",
        gate_criteria: "HIGH sev + 22-rule set + prod code + Bandit HIGH confidence",
      },
    };
    getConfirmedSummary.mockResolvedValue(summary);

    renderOverview();

    // The real confirmed count (3) must render in the hero tile.
    await waitFor(() => {
      const tile = screen.getByText("Confirmed Tier").closest(".bento-cell");
      expect(tile).not.toBeNull();
      expect(tile!.querySelector(".bento-value")?.textContent).toBe("3");
    });

    // The fabricated value (10) must NOT be the Confirmed Tier value.
    const tile = screen.getByText("Confirmed Tier").closest(".bento-cell");
    expect(tile!.querySelector(".bento-value")?.textContent).not.toBe("10");

    // confirmed-summary must be fetched for the latest run (967), not aggregated.
    expect(getConfirmedSummary).toHaveBeenCalledWith(967);
  });

  it("renders 0 with auto-block-safe framing when no confirmed findings", async () => {
    getRuns.mockResolvedValue({ runs: [makeRun(967, 0, 1)] } as RunsResponse);
    getConfirmedSummary.mockResolvedValue({
      run_id: 967,
      total_findings: 1,
      confirmed_tier_count: 0,
      confirmed_tier_pct: 0,
      signals: {},
      auto_block_safe: true,
      precision_context: {
        confirmed_tier_precision: "96.4%",
        false_positive_tolerance: "<4%",
        gate_criteria: "x",
      },
    } as ConfirmedSummary);

    renderOverview();

    await waitFor(() => {
      const tile = screen.getByText("Confirmed Tier").closest(".bento-cell");
      expect(tile!.querySelector(".bento-value")?.textContent).toBe("0");
    });
    expect(screen.getByText(/auto-block safe/i)).toBeInTheDocument();
  });

  it("does not crash and shows empty state when there are no runs", async () => {
    getRuns.mockResolvedValue({ runs: [] } as RunsResponse);

    renderOverview();

    await waitFor(() => {
      expect(screen.getByText(/No scans yet/i)).toBeInTheDocument();
    });
    // confirmed-summary must NOT be fetched when there is no latest run.
    expect(getConfirmedSummary).not.toHaveBeenCalled();
  });
});
