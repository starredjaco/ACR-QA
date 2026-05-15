import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";

describe("Card", () => {
  it("renders children", () => {
    render(<Card><div>content</div></Card>);
    expect(screen.getByText("content")).toBeInTheDocument();
  });

  it("CardTitle renders text", () => {
    render(<CardTitle>My Title</CardTitle>);
    expect(screen.getByText("My Title")).toBeInTheDocument();
  });

  it("CardContent renders children", () => {
    render(<CardContent><p>Body text</p></CardContent>);
    expect(screen.getByText("Body text")).toBeInTheDocument();
  });

  it("CardFooter renders children", () => {
    render(<CardFooter><button>Save</button></CardFooter>);
    expect(screen.getByText("Save")).toBeInTheDocument();
  });

  it("CardHeader + CardTitle compose correctly", () => {
    render(
      <Card>
        <CardHeader><CardTitle>Title here</CardTitle></CardHeader>
        <CardContent>Body here</CardContent>
      </Card>
    );
    expect(screen.getByText("Title here")).toBeInTheDocument();
    expect(screen.getByText("Body here")).toBeInTheDocument();
  });
});
