import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, INTER, glowGreen } from "../theme";

// SCENE — REAL PRODUCT. Ahmed: the tight static crop was clearer but the WIDE view "looked cooler — lots
// going on." So: OPEN WIDE (the whole real dashboard, busy/impressive — sells "I built a big system") then
// Ken-Burns PUSH IN to the key band by the end (legible). Best of both + the motion he judges on.
// Real, live-captured screenshots (2880×1800). Shot A: trust band. Shot B: signed attestation.

const Window: React.FC<{
  src: string;
  startAt: number; // scene frame when this shot's push begins (so it pushes while visible)
  span: number;
  imgWidth: number;
  tx: number;
  top: number;
  originX: number; // % — the region the zoom pushes INTO
  originY: number;
  scaleFrom: number;
  scaleTo: number;
  opacity: number;
}> = ({ src, startAt, span, imgWidth, tx, top, originX, originY, scaleFrom, scaleTo, opacity }) => {
  const frame = useCurrentFrame();
  const sc = interpolate(frame, [startAt, startAt + span], [scaleFrom, scaleTo], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        width: 980,
        height: 612,
        borderRadius: 14,
        overflow: "hidden",
        border: `1px solid ${C.border}`,
        boxShadow: "0 0 0 1px rgba(255,255,255,0.04), 0 30px 90px rgba(0,0,0,0.7)",
        opacity,
      }}
    >
      {/* faux browser chrome — reads as a real app */}
      <div
        style={{
          height: 40,
          backgroundColor: "#0d0d10",
          display: "flex",
          alignItems: "center",
          paddingLeft: 16,
          gap: 8,
          borderBottom: `1px solid ${C.border}`,
        }}
      >
        <div style={{ width: 11, height: 11, borderRadius: "50%", backgroundColor: C.red }} />
        <div style={{ width: 11, height: 11, borderRadius: "50%", backgroundColor: "#eab308" }} />
        <div style={{ width: 11, height: 11, borderRadius: "50%", backgroundColor: C.green }} />
        <span style={{ fontFamily: INTER, fontSize: 16, color: C.muted, marginLeft: 14 }}>
          localhost:8000 — ACR-QA
        </span>
      </div>
      <div style={{ position: "relative", width: "100%", height: 572, overflow: "hidden", backgroundColor: "#0a0a0c" }}>
        <Img
          src={staticFile(src)}
          style={{
            position: "absolute",
            width: imgWidth,
            left: tx,
            top,
            transform: `scale(${sc})`,
            transformOrigin: `${originX}% ${originY}%`,
          }}
        />
      </div>
    </div>
  );
};

export const Dashboard: React.FC = () => {
  const frame = useCurrentFrame();

  const aOp = interpolate(frame, [0, 14, 138, 158], [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const bOp = interpolate(frame, [144, 162], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const capOp = interpolate(frame, [10, 28], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "absolute", top: 96, width: "100%", textAlign: "center", opacity: capOp }}>
        <span style={{ fontFamily: INTER, fontSize: 40, fontWeight: 600, color: C.white }}>
          Not a script — a <span style={{ color: C.green, ...glowGreen(18) }}>real, running product.</span>
        </span>
      </div>

      {/* Shot A — open on the WHOLE dashboard (busy/cool), push into the trust band (96.4% · 8/8 · 0 critical) */}
      <Window
        src="shots/overview.png"
        startAt={0}
        span={150}
        imgWidth={1040}
        tx={-30}
        top={-12}
        originX={46}
        originY={20}
        scaleFrom={1.0}
        scaleTo={1.62}
        opacity={aOp}
      />

      {/* Shot B — open on the whole attestation page, push into the green Signature-Verified band */}
      <Window
        src="shots/attestation.png"
        startAt={144}
        span={96}
        imgWidth={1040}
        tx={-30}
        top={-150}
        originX={42}
        originY={45}
        scaleFrom={1.0}
        scaleTo={1.55}
        opacity={bOp}
      />

      <div style={{ position: "absolute", bottom: 92, width: "100%", textAlign: "center", opacity: bOp }}>
        <span style={{ fontFamily: INTER, fontSize: 34, fontWeight: 500, color: C.muted }}>
          Every scan: <span style={{ color: C.white }}>signed, auditable, reproducible.</span>
        </span>
      </div>
    </AbsoluteFill>
  );
};
