import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, INTER, MONO, SPRING_TIGHT, glowGreen } from "../theme";

// SCENE — UNDER THE HOOD (the backend/DevOps flex — richer ON PURPOSE here). Real topology:
// FastAPI control plane → Redis broker → 4 Celery workers, EACH spawning its own ephemeral,
// egress-filtered Docker sandbox → Postgres. Tasks flow through it (the motion). 4 clean columns
// keep the density organized; a backend recruiter can pause and read the whole distributed system.

type Pt = { x: number; y: number };
const API: Pt = { x: 540, y: 188 };
const REDIS: Pt = { x: 540, y: 348 };
const COLX = [198, 426, 654, 882];
const WORKERS: Pt[] = COLX.map((x) => ({ x, y: 500 }));
const SANDBOX: Pt[] = COLX.map((x) => ({ x, y: 648 }));
const DB: Pt = { x: 540, y: 808 };

const SEGMENTS: [Pt, Pt][] = [
  [{ x: API.x, y: API.y + 38 }, { x: REDIS.x, y: REDIS.y - 36 }],
  ...WORKERS.map((w) => [{ x: REDIS.x, y: REDIS.y + 36 }, { x: w.x, y: w.y - 35 }] as [Pt, Pt]),
  ...WORKERS.map((w, i) => [{ x: w.x, y: w.y + 35 }, { x: SANDBOX[i].x, y: SANDBOX[i].y - 35 }] as [Pt, Pt]),
  ...SANDBOX.map((s) => [{ x: s.x, y: s.y + 35 }, { x: DB.x, y: DB.y - 38 }] as [Pt, Pt]),
];

const Dots: React.FC = () => {
  const frame = useCurrentFrame();
  const PERIOD = 44;
  const dots: { x: number; y: number; o: number }[] = [];
  SEGMENTS.forEach(([a, b], si) => {
    for (let i = 0; i < 2; i++) {
      const t = ((frame * 1.0 + i * (PERIOD / 2) + si * 6) % PERIOD) / PERIOD;
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
            left: d.x - 4,
            top: d.y - 4,
            width: 9,
            height: 9,
            borderRadius: "50%",
            backgroundColor: C.green,
            opacity: 0.25 + d.o * 0.75,
            boxShadow: "0 0 9px rgba(34,197,94,0.7)",
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
}> = ({ c, w, h = 76, label, sub, appearAt, accent, ephemeral, small }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = frame < appearAt ? 0 : spring({ frame: frame - appearAt, fps, config: SPRING_TIGHT });
  const breathe = ephemeral ? 0.82 + 0.18 * Math.abs(Math.sin((frame + c.x) / 19)) : 1;
  return (
    <div
      style={{
        position: "absolute",
        left: c.x - w / 2,
        top: c.y - h / 2,
        width: w,
        height: h,
        borderRadius: 11,
        border: `1px solid ${accent}`,
        background: "rgba(10,12,16,0.92)",
        boxShadow: `0 0 22px ${accent}30`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity: s * (ephemeral ? breathe : 1),
        transform: `scale(${0.9 + s * 0.1})`,
      }}
    >
      <span style={{ fontFamily: MONO, fontSize: small ? 20 : 25, fontWeight: 700, color: "#fff" }}>{label}</span>
      <span style={{ fontFamily: INTER, fontSize: small ? 12.5 : 16, color: C.muted, marginTop: 2, textAlign: "center", lineHeight: 1.15 }}>
        {sub}
      </span>
    </div>
  );
};

export const Architecture: React.FC = () => {
  const frame = useCurrentFrame();
  const title = interpolate(frame, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cap = interpolate(frame, [156, 176], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 70, width: "100%", textAlign: "center", opacity: title }}>
        <span style={{ fontFamily: INTER, fontSize: 40, fontWeight: 700, color: C.white }}>
          Under the hood: a <span style={{ color: C.green, ...glowGreen(18) }}>distributed engine.</span>
        </span>
      </div>

      {frame > 52 ? SEGMENTS.map((seg, i) => <Line key={i} a={seg[0]} b={seg[1]} />) : null}
      {frame > 60 ? <Dots /> : null}

      <Box c={API} w={470} label="FastAPI" sub="control plane · 52 async endpoints · SSE" appearAt={16} accent={C.blue} />
      <Box c={REDIS} w={410} label="Redis" sub="broker · result backend · cache" appearAt={34} accent={C.blue} />
      {WORKERS.map((w, i) => (
        <Box key={`w${i}`} c={w} w={202} h={70} small label="Celery" sub="worker" appearAt={56 + i * 7} accent={C.blue} />
      ))}
      {SANDBOX.map((s, i) => (
        <Box
          key={`s${i}`}
          c={s}
          w={202}
          h={72}
          small
          label="Docker"
          sub="ephemeral · egress-filtered"
          appearAt={86 + i * 7}
          accent={C.green}
          ephemeral
        />
      ))}
      <Box c={DB} w={410} label="PostgreSQL" sub="provenance · signed attestations" appearAt={120} accent={C.blue} />

      <div style={{ position: "absolute", bottom: 50, width: "100%", textAlign: "center", opacity: cap }}>
        <span style={{ fontFamily: INTER, fontSize: 29, fontWeight: 500, color: C.muted }}>
          <span style={{ color: C.white }}>4 workers</span>, each spinning an isolated Docker sandbox — untrusted code, safely, at scale.
        </span>
      </div>
    </AbsoluteFill>
  );
};
