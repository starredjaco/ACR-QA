import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, INTER, MONO, SPRING_TIGHT, glowGreen } from "../theme";
import { PipelineArrow } from "../components/PipelineArrow";
import { FunnelFlow } from "../components/Particles";
import { CountUp, Breathe } from "../components/Kinetic";

const Stage: React.FC<{
  appearAt: number;
  labelTop?: string;
  countTo: number;
  numberSize: number;
  numberColor: string;
  sub?: string;
  pulse?: boolean;
}> = ({ appearAt, labelTop, countTo, numberSize, numberColor, sub, pulse }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < appearAt) return null;
  const s = spring({ frame: frame - appearAt, fps, config: SPRING_TIGHT });
  const numberEl = (
    <div
      style={{
        fontFamily: MONO,
        fontSize: numberSize,
        fontWeight: 700,
        color: numberColor,
        lineHeight: 1,
        ...(pulse ? glowGreen(50) : {}),
      }}
    >
      <CountUp to={countTo} appearAt={appearAt} dur={pulse ? 44 : 30} />
    </div>
  );
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        opacity: s,
        transform: `translateY(${(1 - s) * 12}px)`,
      }}
    >
      {labelTop ? (
        <div style={{ fontFamily: INTER, fontSize: 30, color: C.blue, letterSpacing: 1, marginBottom: 4 }}>
          {labelTop}
        </div>
      ) : null}
      {pulse ? <Breathe amp={0.022} period={56}>{numberEl}</Breathe> : numberEl}
      {sub ? (
        <div style={{ fontFamily: INTER, fontSize: 32, color: C.muted, marginTop: 6 }}>{sub}</div>
      ) : null}
    </div>
  );
};

const NoiseDots: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame < 360 || frame > 410) return null;
  const p = interpolate(frame, [360, 400], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const dots = Array.from({ length: 10 }, (_, i) => {
    const left = i < 5;
    const baseY = 360 + (i % 5) * 70;
    const dir = left ? -1 : 1;
    return { x: 540 + dir * (60 + p * 220), y: baseY, op: 1 - p };
  });
  return (
    <>
      {dots.map((d, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: d.x,
            top: d.y,
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: C.red,
            opacity: d.op * 0.8,
          }}
        />
      ))}
    </>
  );
};

const SummaryLine: React.FC<{ appearAt: number; text: string; color: string; size: number }> = ({
  appearAt,
  text,
  color,
  size,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < appearAt) return null;
  const s = spring({ frame: frame - appearAt, fps, config: SPRING_TIGHT });
  return (
    <div
      style={{
        fontFamily: INTER,
        fontSize: size,
        color,
        textAlign: "center",
        opacity: s,
        transform: `translateY(${(1 - s) * 10}px)`,
        ...(color === C.green ? glowGreen(26) : {}),
      }}
    >
      {text}
    </div>
  );
};

// SCENE 3 — THE PIPELINE · frames 600–1020 (relative 0–420).
export const Pipeline: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const aIn = spring({ frame, fps, config: SPRING_TIGHT });
  const aSub = spring({ frame: frame - 30, fps, config: SPRING_TIGHT });
  const titleTop = interpolate(frame, [50, 75], [410, 22], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleScale = frame < 50 ? 1 : interpolate(frame, [50, 75], [1, 0.5], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const titleOpacity = frame < 50 ? 1 : interpolate(frame, [50, 75], [1, 0.2], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill>
      {/* PART A — identity, then dims + slides to top third */}
      <div
        style={{
          position: "absolute",
          top: titleTop,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 12,
          opacity: titleOpacity,
          transform: `scale(${titleScale})`,
        }}
      >
        <div style={{ fontFamily: MONO, fontSize: 72, fontWeight: 700, color: C.green, opacity: aIn }}>
          ACR-QA
        </div>
        {frame >= 30 ? (
          <div style={{ fontFamily: INTER, fontSize: 40, color: C.white, opacity: aSub }}>
            No LLM. No hallucinations. Deterministic.
          </div>
        ) : null}
      </div>

      {/* Living particle flow behind the funnel */}
      {frame >= 45 ? <FunnelFlow /> : null}

      {/* PART B — funnel */}
      <div
        style={{
          position: "absolute",
          top: 150,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 4,
        }}
      >
        <Stage appearAt={45} countTo={1942} numberSize={78} numberColor={C.white} sub="raw findings from all scanners" />
        <PipelineArrow drawStart={80} drawEnd={108} height={46} color={C.blue} />
        <Stage appearAt={112} labelTop="[SEVERITY GATE]" countTo={219} numberSize={78} numberColor={C.white} />
        <PipelineArrow drawStart={146} drawEnd={172} height={46} color={C.blue} />
        <Stage appearAt={178} labelTop="[22 CURATED RULES]" countTo={151} numberSize={78} numberColor={C.white} />
        <PipelineArrow drawStart={208} drawEnd={232} height={46} color={C.blue} />
        <Stage appearAt={240} labelTop="[TAINT: HTTP-source confirmed]" countTo={55} numberSize={118} numberColor={C.green} pulse />
      </div>

      <NoiseDots />

      {/* Summary lines */}
      <div
        style={{
          position: "absolute",
          bottom: 34,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 8,
        }}
      >
        <SummaryLine appearAt={262} text="55 Confirmed · 96.4% precision" color={C.white} size={42} />
        <SummaryLine appearAt={274} text="100% CVE recall — 8 / 8 real CVEs" color={C.green} size={46} />
        <SummaryLine appearAt={286} text="No LLM made the call" color={C.white} size={38} />
      </div>
    </AbsoluteFill>
  );
};
