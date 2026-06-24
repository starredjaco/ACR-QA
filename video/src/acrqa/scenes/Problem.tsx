import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, INTER, MONO, SPRING_TIGHT, glowWhite } from "../theme";
import { Terminal } from "../components/Terminal";
import { Reveal } from "../components/Reveal";

const RULES: [string, string, string, string][] = [
  ["bandit", "B101", "assert usage", "medium"],
  ["semgrep", "S027", "SQL injection", "high"],
  ["ruff", "E501", "line too long", "low"],
  ["bandit", "B602", "subprocess", "high"],
  ["semgrep", "S105", "hardcoded secret", "high"],
  ["ruff", "F401", "unused import", "low"],
  ["bandit", "B608", "hardcoded SQL", "high"],
  ["semgrep", "S321", "insecure ftp", "medium"],
  ["ruff", "E711", "compare to None", "low"],
  ["bandit", "B303", "weak MD5 hash", "medium"],
];

// 30 deterministic mock warning lines.
const LINES = Array.from({ length: 30 }, (_, i) => {
  const r = RULES[i % RULES.length];
  const ln = 12 + ((i * 137) % 920);
  return `WARNING  ${r[0].padEnd(8)} ${r[1]}  ${r[2].padEnd(18)} ${r[3].padEnd(7)} ln ${ln}`;
});

// SCENE 2 — THE PROBLEM + JARGON TRANSLATION · 270f. The pain (false positives) then the one-line
// outcome translation of "SAST" so the mixed feed (engineers + recruiters) both parse it instantly.
export const Problem: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enter = spring({ frame, fps, config: SPRING_TIGHT });
  const slideUp = (1 - enter) * 220; // springs in from bottom

  const count = Math.round(
    interpolate(frame, [6, 70], [0, 1942], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
  );

  const dimmed = frame >= 92;
  const scroll = interpolate(frame, [30, 270], [0, -360], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          transform: `translateY(${slideUp}px)`,
          opacity: dimmed ? 0.25 : 1,
          boxShadow: dimmed ? "none" : "0 0 80px rgba(0,0,0,0.6)",
        }}
      >
        <Terminal width={900} height={760}>
          <div style={{ position: "absolute", inset: 0, padding: "26px 30px", overflow: "hidden" }}>
            <div style={{ transform: `translateY(${scroll}px)` }}>
              {LINES.map((l, i) => (
                <div
                  key={i}
                  style={{
                    fontFamily: MONO,
                    fontSize: 25,
                    color: C.muted,
                    lineHeight: 1.7,
                    whiteSpace: "pre",
                  }}
                >
                  {l}
                </div>
              ))}
            </div>
          </div>
          <div
            style={{
              position: "absolute",
              top: 22,
              right: 30,
              fontFamily: MONO,
              fontSize: 48,
              color: C.white,
              backgroundColor: "#000000",
              padding: "4px 10px",
            }}
          >
            {count.toLocaleString()}
          </div>
        </Terminal>
      </div>

      <div
        style={{
          position: "absolute",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 28,
        }}
      >
        <Reveal appearAt={100}>
          <div
            style={{
              fontFamily: INTER,
              fontSize: 54,
              color: C.white,
              textAlign: "center",
              ...glowWhite(20),
            }}
          >
            SAST scanners drown you in false positives.
          </div>
        </Reveal>
        <Reveal appearAt={170}>
          <div style={{ fontFamily: INTER, fontSize: 50, color: C.white, textAlign: "center", maxWidth: 880, lineHeight: 1.3 }}>
            Mine fires a <span style={{ color: C.green, ...glowWhite(0) }}>real exploit</span> at every finding —
            only what actually <span style={{ color: C.green }}>breaks</span> survives.
          </div>
        </Reveal>
      </div>
    </AbsoluteFill>
  );
};
