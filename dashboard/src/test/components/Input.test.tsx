import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Input } from "@/components/ui/input";

describe("Input", () => {
  it("renders with placeholder", () => {
    render(<Input placeholder="Search…" />);
    expect(screen.getByPlaceholderText("Search…")).toBeInTheDocument();
  });

  it("fires onChange", () => {
    const handler = vi.fn();
    render(<Input onChange={handler} />);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "hello" } });
    expect(handler).toHaveBeenCalled();
  });

  it("is disabled when prop set", () => {
    render(<Input disabled />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("reflects controlled value", () => {
    render(<Input value="preset" onChange={vi.fn()} />);
    expect(screen.getByDisplayValue("preset")).toBeInTheDocument();
  });

  it("has type=password for password inputs", () => {
    render(<Input type="password" />);
    const el = document.querySelector("input[type='password']");
    expect(el).not.toBeNull();
  });
});
