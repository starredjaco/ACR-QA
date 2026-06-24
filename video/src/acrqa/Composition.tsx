import { AbsoluteFill, interpolate, Series, useCurrentFrame } from "remotion";
import { C } from "./theme";
import { Background } from "./components/Background";
import { SceneFade } from "./components/Reveal";
import { Hook } from "./scenes/Hook";
import { Problem } from "./scenes/Problem";
import { Scan } from "./scenes/Scan";
import { ExploitProof } from "./scenes/ExploitProof";
import { Architecture } from "./scenes/Architecture";
import { Dashboard } from "./scenes/Dashboard";
import { Benchmark } from "./scenes/Benchmark";
import { Moat } from "./scenes/Moat";
import { Numbers } from "./scenes/Numbers";
import { EndCard } from "./scenes/EndCard";

// Subtle scrubber at the very bottom — fills over the whole 2700 frames. Quiet sense of motion + cohesion.
const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const pct = interpolate(frame, [0, 2700], [0, 100], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", bottom: 0, left: 0, width: "100%", height: 3 }}>
      <div style={{ position: "absolute", inset: 0, backgroundColor: "rgba(255,255,255,0.06)" }} />
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          height: "100%",
          width: `${pct}%`,
          backgroundColor: C.green,
          boxShadow: "0 0 12px rgba(34,197,94,0.7)",
        }}
      />
    </div>
  );
};

// Beat sheet (2700f @ 30fps) — PROOF-FIRST, then the ENGINEERING (backend/DevOps job pivot):
// Hook(contrarian) → Problem(jargon) → Scan(REAL money shot) → Exploit(red→green) →
// Architecture(the distributed engine: FastAPI·Celery/Redis·Docker sandboxes·Postgres) →
// Dashboard(REAL product) → Benchmark(#1@$0) → Moat(trade-off breaker) → Numbers(solo) → EndCard(CTA).
const SCENES: { c: React.FC; d: number; dir: 1 | -1; inLen?: number; outLen?: number }[] = [
  { c: Hook, d: 150, dir: 1 },
  { c: Problem, d: 240, dir: -1 },
  { c: Scan, d: 365, dir: 1 },
  { c: ExploitProof, d: 460, dir: -1 },
  { c: Architecture, d: 270, dir: 1 },
  { c: Dashboard, d: 240, dir: -1 },
  { c: Benchmark, d: 255, dir: 1 },
  { c: Moat, d: 240, dir: -1 },
  { c: Numbers, d: 180, dir: 1 },
  { c: EndCard, d: 300, dir: -1, outLen: 1 },
];

export const MainComposition: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#070708" }}>
      <Background />
      <Series>
        {SCENES.map(({ c: Scene, d, dir, inLen, outLen }, i) => (
          <Series.Sequence key={i} durationInFrames={d}>
            <SceneFade durationInFrames={d} dir={dir} inLen={inLen} outLen={outLen}>
              <Scene />
            </SceneFade>
          </Series.Sequence>
        ))}
      </Series>
      <ProgressBar />
    </AbsoluteFill>
  );
};
