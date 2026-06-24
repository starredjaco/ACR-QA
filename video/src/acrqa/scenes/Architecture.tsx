import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, INTER, MONO, SPRING_TIGHT, glowGreen } from "../theme";

// SCENE — UNDER THE HOOD (added for the backend/DevOps job pivot — research: the video must show the
// DISTRIBUTED SYSTEM, not just the security result). A live pipeline with tasks flowing through it:
// FastAPI control plane → Celery/Redis data plane → ephemeral Docker sandboxes → Postgres. The flow
// itself is the motion. Reframes the same project as a platform-infrastructure achievement.

type Pt = { x: number; y: number };
const API: Pt = { x: 540, y: 250 };
const QUEUE: Pt = { x: 540, y: 440 };
const SBX: Pt[] = [
  { x: 250, y: 638 },
  { x: 540, y: 638 },
  { x: 830, y: 638 },
];
const DB: Pt = { x: 540, y: 832 };

const SEGMENTS: [Pt, Pt][] = [
  [{ x: API.x, y: API.y + 44 }, { x: QUEUE.x, y: QUEUE.y - 44 }],
  ...SBX.map((s) => [{ x: QUEUE.x, y: QUEUE.y + 44 }, { x: s.x, y: s.y - 40 }] as [Pt, Pt]),
  ...SBX.map((s) => [{ x: s.x, y: s.y + 40 }, { x: DB.x, y: DB.y - 44 }] as [Pt, Pt]),
];

// Continuous task-dots travelling each segment — the "engine running" motion.
const Dots: React.FC = () => {
  const frame = useCurrentFrame();
  const PERIOD = 46;
  const PER_SEG = 2;
  const dots: { x: number; y: number; o: number }[] = [];
  SEGMENTS.forEach(([a, b], si) => {
    for (let i = 0; i < PER_SEG; i++) {
      const t = (((frame * 1.0 + i * (PERIOD / PER_SEG) + si * 9) % PERIOD) / PERIOD);
      dots.push({
        x: a.x + (b.x - a.x) * t,
        y: a.y + (b.y - a.y) * t,
        o: Math.sin(t * Math.PI), // fade in/out along the path
      });
    }
  });
  return (
    <>
      {dots.map((d, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: d.x - 5,
            top: d.y - 5,
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: C.green,
            opacity: 0.25 + d.o * 0.75,
            boxShadow: "0 0 10px rgba(34,197,94,0.7)",
          }}
        />
      ))}
    </>
  );
};

const Line: React.FC<{ a: Pt; b: Pt }> = ({ a, b }) => {
  const len = Math.hypot(b.x - a.x, b.y - a.y);
  const ang = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
  return (
    <div
      style={{
        position: "absolute",
        left: a.x,
        top: a.y,
        width: len,
        height: 2,
        backgroundColor: "rgba(120,140,170,0.22)",
        transform: `rotate(${ang}deg)`,
        transformOrigin: "0 50%",
      }}
    />
  );
};

const Box: React.FC<{
  c: Pt;
  w: number;
  label: string;
  sub: string;
  appearAt: number;
  accent: string;
  ephemeral?: boolean;
}> = ({ c, w, label, sub, appearAt, accent, ephemeral }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = frame < appearAt ? 0 : spring({ frame: frame - appearAt, fps, config: SPRING_TIGHT });
  // ephemeral sandboxes breathe (spin up/down feel)
  const breathe = ephemeral ? 0.85 + 0.15 * Math.abs(Math.sin((frame + c.x) / 22)) : 1;
  const h = 80;
  return (
    <div
      style={{
        position: "absolute",
        left: c.x - w / 2,
        top: c.y - h / 2,
        width: w,
        height: h,
        borderRadius: 12,
        border: `1px solid ${accent}`,
        background: "rgba(10,12,16,0.92)",
        boxShadow: `0 0 26px ${accent}33`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity: s * (ephemeral ? breathe : 1),
        transform: `scale(${0.9 + s * 0.1})`,
      }}
    >
      <span style={{ fontFamily: MONO, fontSize: 26, fontWeight: 700, color: "#fff" }}>{label}</span>
      <span style={{ fontFamily: INTER, fontSize: 17, color: C.muted, marginTop: 3 }}>{sub}</span>
    </div>
  );
};

export const Architecture: React.FC = () => {
  const frame = useCurrentFrame();
  const title = interpolate(frame, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cap = interpolate(frame, [150, 170], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const linesOn = frame > 50;

  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 92, width: "100%", textAlign: "center", opacity: title }}>
        <span style={{ fontFamily: INTER, fontSize: 42, fontWeight: 700, color: C.white }}>
          Under the hood: a <span style={{ color: C.green, ...glowGreen(18) }}>distributed engine.</span>
        </span>
      </div>

      {linesOn ? SEGMENTS.map((seg, i) => <Line key={i} a={seg[0]} b={seg[1]} />) : null}
      {frame > 58 ? <Dots /> : null}

      <Box c={API} w={420} label="FastAPI" sub="control plane · async ingestion" appearAt={20} accent={C.blue} />
      <Box c={QUEUE} w={440} label="Celery + Redis" sub="task queue · fault-tolerant" appearAt={40} accent={C.blue} />
      <Box c={SBX[0]} w={230} label="Docker" sub="sandbox" appearAt={64} accent={C.green} ephemeral />
      <Box c={SBX[1]} w={230} label="Docker" sub="sandbox" appearAt={72} accent={C.green} ephemeral />
      <Box c={SBX[2]} w={230} label="Docker" sub="sandbox" appearAt={80} accent={C.green} ephemeral />
      <Box c={DB} w={360} label="PostgreSQL" sub="provenance · results" appearAt={104} accent={C.blue} />

      <div style={{ position: "absolute", bottom: 70, width: "100%", textAlign: "center", opacity: cap }}>
        <span style={{ fontFamily: INTER, fontSize: 30, fontWeight: 500, color: C.muted }}>
          Spins up <span style={{ color: C.white }}>ephemeral sandboxes</span> to run untrusted code safely, at scale.
        </span>
      </div>
    </AbsoluteFill>
  );
};
