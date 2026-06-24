import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, INTER, MONO, glowGreen } from "../theme";
import { Reveal } from "../components/Reveal";

// SCENE — THE BENCHMARK. Empirical visual proof (the #1 dev-tool launch convention): an animated
// horizontal bar chart. SAST tools stall short; ACR-QA blooms green past the $62 frontier agents — at $0.
// All values are the verified RealVuln 2026 recall figures.
const ROWS: { label: string; value: number; cost: string; color: string; highlight?: boolean }[] = [
  { label: "SonarQube", value: 5.2, cost: "paid", color: C.muted },
  { label: "Snyk", value: 14.9, cost: "paid", color: C.muted },
  { label: "Semgrep", value: 17.6, cost: "paid", color: C.muted },
  { label: "Claude Opus 4.8", value: 51.7, cost: "~$30", color: C.blue },
  { label: "Gemini 3.1 Pro", value: 52.6, cost: "~$20", color: C.blue },
  { label: "GPT-5.5 agent", value: 58.2, cost: "$62", color: C.blue },
  { label: "ACR-QA", value: 58.8, cost: "$0", color: C.green, highlight: true },
];

const MAXW = 540;
const SCALE = 62; // % that maps to full bar width

const Bar: React.FC<{ row: (typeof ROWS)[number]; appearAt: number }> = ({ row, appearAt }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p =
    frame < appearAt ? 0 : spring({ frame: frame - appearAt, fps, config: { mass: 1, damping: 30, stiffness: 90 } });
  const w = (row.value / SCALE) * MAXW * p;
  const shown = (row.value * p).toFixed(1);
  return (
    <div style={{ display: "flex", alignItems: "center", height: 74, opacity: p > 0.02 ? 1 : 0 }}>
      <div
        style={{
          width: 300,
          textAlign: "right",
          paddingRight: 24,
          fontFamily: INTER,
          fontSize: row.highlight ? 34 : 30,
          fontWeight: row.highlight ? 700 : 500,
          color: row.highlight ? C.green : C.white,
          ...(row.highlight ? glowGreen(20) : {}),
        }}
      >
        {row.label}
      </div>
      <div style={{ width: MAXW, height: 40, position: "relative" }}>
        <div style={{ position: "absolute", inset: 0, backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 6 }} />
        <div
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            height: "100%",
            width: w,
            borderRadius: 6,
            background: row.highlight
              ? `linear-gradient(90deg, #16a34a, ${C.green})`
              : row.color,
            boxShadow: row.highlight
              ? "0 0 18px rgba(34,197,94,0.5), 0 0 60px rgba(34,197,94,0.18)"
              : "none",
          }}
        />
      </div>
      <div
        style={{
          width: 150,
          paddingLeft: 18,
          fontFamily: MONO,
          fontSize: row.highlight ? 38 : 30,
          fontWeight: 700,
          letterSpacing: "-0.03em",
          color: row.highlight ? C.green : C.white,
          ...(row.highlight ? glowGreen(20) : {}),
        }}
      >
        {shown}%
      </div>
    </div>
  );
};

export const Benchmark: React.FC = () => {
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "absolute", top: 130, width: "100%", textAlign: "center" }}>
        <Reveal appearAt={6}>
          <div style={{ fontFamily: INTER, fontSize: 30, fontWeight: 500, letterSpacing: "0.05em", color: C.muted }}>
            RealVuln 2026 · recall on 22 real-world vulnerable repos
          </div>
        </Reveal>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 7, marginTop: 30 }}>
        {ROWS.map((row, i) => (
          <Bar key={row.label} row={row} appearAt={30 + i * 20} />
        ))}
      </div>

      <div style={{ position: "absolute", bottom: 96, width: "100%", textAlign: "center" }}>
        <Reveal appearAt={185}>
          <div style={{ fontFamily: INTER, fontSize: 42, fontWeight: 600, color: C.white }}>
            #1 recall — at <span style={{ color: C.green, ...glowGreen(18) }}>$0</span>, not{" "}
            <span style={{ color: C.green, ...glowGreen(18) }}>$62</span>.
          </div>
        </Reveal>
        <Reveal appearAt={205}>
          <div style={{ fontFamily: INTER, fontSize: 28, fontWeight: 500, color: C.muted, marginTop: 12 }}>
            And identical every run. The LLMs aren&apos;t.
          </div>
        </Reveal>
      </div>
    </AbsoluteFill>
  );
};
