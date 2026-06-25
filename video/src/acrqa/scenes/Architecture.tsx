import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, INTER, MONO, SPRING_TIGHT, glowGreen } from "../theme";

// SCENE — UNDER THE HOOD (backend/DevOps signal). The REAL distributed pipeline: FastAPI control plane →
// Redis broker → 4 Celery workers (the system's real concurrency) → each spins an ephemeral Docker
// sandbox → Postgres. Tasks flow through it (the motion). Shows worker-pool concurrency a recruiter asks about.

type Pt = { x: number; y: number };
const API: Pt = { x: 540, y: 212 };
const REDIS: Pt = { x: 540, y: 388 };
const WORKERS: Pt[] = [
  { x: 213, y: 588 },
  { x: 431, y: 588 },
  { x: 649, y: 588 },
  { x: 867, y: 588 },
];
const DB: Pt = { x: 540, y: 802 };

const SEGMENTS: [Pt, Pt][] = [
  [{ x: API.x, y: API.y + 40 }, { x: REDIS.x, y: REDIS.y - 40 }],
  ...WORKERS.map((w) => [{ x: REDIS.x, y: REDIS.y + 40 }, { x: w.x, y: w.y - 44 }] as [Pt, Pt]),
  ...WORKERS.map((w) => [{ x: w.x, y: w.y + 44 }, { x: DB.x, y: DB.y - 40 }] as [Pt, Pt]),
];

const Dots: React.FC = () => {
  const frame = useCurrentFrame();
  const PERIOD = 46;
  const PER_SEG = 2;
  const dots: { x: number; y: number; o: number }[] = [];
  SEGMENTS.forEach(([a, b], si) => {
    for (let i = 0; i < PER_SEG; i++) {
      const t = ((frame * 1.0 + i * (PERIOD / PER_SEG) + si * 7) % PERIOD) / PERIOD;
      dots.push({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, o: Math.sin(t * Math.PI) });
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
  h?: number;
  label: string;
  sub: string;
  appearAt: number;
  accent: string;
  ephemeral?: boolean;
  small?: boolean;
}> = ({ c, w, h = 80, label, sub, appearAt, accent, ephemeral, small }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = frame < appearAt ? 0 : spring({ frame: frame - appearAt, fps, config: SPRING_TIGHT });
  const breathe = ephemeral ? 0.82 + 0.18 * Math.abs(Math.sin((frame + c.x) / 20)) : 1;
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
      <span style={{ fontFamily: MONO, fontSize: small ? 21 : 26, fontWeight: 700, color: "#fff" }}>{label}</span>
      <span style={{ fontFamily: INTER, fontSize: small ? 14 : 17, color: C.muted, marginTop: 3 }}>{sub}</span>
    </div>
  );
};

export const Architecture: React.FC = () => {
  const frame = useCurrentFrame();
  const title = interpolate(frame, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cap = interpolate(frame, [150, 170], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 88, width: "100%", textAlign: "center", opacity: title }}>
        <span style={{ fontFamily: INTER, fontSize: 42, fontWeight: 700, color: C.white }}>
          Under the hood: a <span style={{ color: C.green, ...glowGreen(18) }}>distributed engine.</span>
        </span>
      </div>

      {frame > 50 ? SEGMENTS.map((seg, i) => <Line key={i} a={seg[0]} b={seg[1]} />) : null}
      {frame > 58 ? <Dots /> : null}

      <Box c={API} w={420} label="FastAPI" sub="control plane · async ingestion" appearAt={18} accent={C.blue} />
      <Box c={REDIS} w={360} label="Redis" sub="broker · task queue" appearAt={38} accent={C.blue} />
      {WORKERS.map((w, i) => (
        <Box
          key={i}
          c={w}
          w={198}
          h={84}
          small
          label="Celery"
          sub="worker · Docker sandbox"
          appearAt={60 + i * 8}
          accent={C.green}
          ephemeral
        />
      ))}
      <Box c={DB} w={360} label="PostgreSQL" sub="provenance · results" appearAt={104} accent={C.blue} />

      <div style={{ position: "absolute", bottom: 64, width: "100%", textAlign: "center", opacity: cap }}>
        <span style={{ fontFamily: INTER, fontSize: 30, fontWeight: 500, color: C.muted }}>
          <span style={{ color: C.white }}>4 Celery workers</span>, each in an isolated Docker sandbox — untrusted code, safely, at scale.
        </span>
      </div>
    </AbsoluteFill>
  );
};
