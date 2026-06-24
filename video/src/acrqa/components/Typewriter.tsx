import { Fragment } from "react";
import { useCurrentFrame } from "remotion";
import { C, MONO } from "../theme";

export type TWLine = { text: string; color: string; bold?: boolean; pauseAfter?: number };

// Deterministic typewriter: derives everything from useCurrentFrame() — no Math.random()/Date.now().
// Types 1 char/frame; each line is followed by `pauseAfter` (default 15) frames. A white block cursor
// blinks (toggles every 8 frames) at the active position — including during pauses (the tension beat).
function renderChecks(text: string) {
  if (!text.includes("✓")) return text;
  const parts = text.split("✓");
  return parts.map((p, i) => (
    <Fragment key={i}>
      {p}
      {i < parts.length - 1 ? <span style={{ color: C.green }}>✓</span> : null}
    </Fragment>
  ));
}

export const Typewriter: React.FC<{
  lines: TWLine[];
  startFrame: number;
  fontSize?: number;
  defaultPause?: number;
}> = ({ lines, startFrame, fontSize = 36, defaultPause = 15 }) => {
  const frame = useCurrentFrame();
  const elapsed = Math.max(0, frame - startFrame);

  let acc = 0;
  let activeLine = lines.length; // lines.length => everything typed
  let typedInActive = 0;
  for (let i = 0; i < lines.length; i++) {
    const typeDur = lines[i].text.length;
    const pause = lines[i].pauseAfter ?? defaultPause;
    if (elapsed < acc + typeDur) {
      activeLine = i;
      typedInActive = elapsed - acc;
      break;
    }
    if (elapsed < acc + typeDur + pause) {
      activeLine = i;
      typedInActive = lines[i].text.length; // fully typed, sitting in its pause
      break;
    }
    acc += typeDur + pause;
  }

  const allDone = activeLine >= lines.length;
  const cursorLine = allDone ? lines.length - 1 : activeLine;
  const cursorOn = Math.floor(frame / 8) % 2 === 0;

  return (
    <div style={{ fontFamily: MONO, fontSize, lineHeight: 1.6, whiteSpace: "pre" }}>
      {lines.map((ln, i) => {
        if (!allDone && i > activeLine) return null;
        const fullyTyped = allDone || i < activeLine;
        const shown = fullyTyped ? ln.text : ln.text.slice(0, typedInActive);
        const showCursor = i === cursorLine && cursorOn;
        return (
          <div
            key={i}
            style={{
              color: ln.color,
              fontWeight: ln.bold ? 700 : 400,
              minHeight: fontSize * 1.6,
            }}
          >
            {renderChecks(shown)}
            {showCursor ? (
              <span
                style={{
                  display: "inline-block",
                  width: 12,
                  height: Math.round(fontSize * 0.62),
                  backgroundColor: C.white,
                  verticalAlign: "middle",
                  marginLeft: 3,
                }}
              />
            ) : null}
          </div>
        );
      })}
    </div>
  );
};
