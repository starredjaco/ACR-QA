import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ScanCard } from "@/components/scans/ScanCard";
import { MemoryRouter } from "react-router-dom";
import type { Run } from "@/lib/api";

const baseRun: Run = {
  id: 42,
  repo_name: "my-service",
  pr_number: null,
  status: "completed",
  started_at: "2024-06-01T10:00:00Z",
  total_findings: 5,
  high_count: 2,
  medium_count: 2,
  low_count: 1,
};

function wrap(node: React.ReactNode) {
  return render(<MemoryRouter>{node}</MemoryRouter>);
}

describe("ScanCard", () => {
  it("renders repo name", () => {
    wrap(<ScanCard run={baseRun} />);
    expect(screen.getByText("my-service")).toBeInTheDocument();
  });

  it("renders completed status", () => {
    wrap(<ScanCard run={baseRun} />);
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
  });

  it("renders total findings count", () => {
    wrap(<ScanCard run={baseRun} />);
    expect(screen.getByText("5 findings")).toBeInTheDocument();
  });

  it("renders high count badge", () => {
    wrap(<ScanCard run={baseRun} />);
    expect(screen.getByText(/2 HIGH/i)).toBeInTheDocument();
  });

  it("is a link to the run detail page", () => {
    wrap(<ScanCard run={baseRun} />);
    const link = screen.getByRole("link");
    expect(link.getAttribute("href")).toBe("/runs/42");
  });

  it("renders running status", () => {
    wrap(<ScanCard run={{ ...baseRun, status: "running" }} />);
    expect(screen.getByText(/running/i)).toBeInTheDocument();
  });

  it("does not render HIGH badge when high_count is 0", () => {
    wrap(<ScanCard run={{ ...baseRun, high_count: 0 }} />);
    expect(screen.queryByText(/HIGH/)).not.toBeInTheDocument();
  });
});
