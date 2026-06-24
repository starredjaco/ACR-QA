import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, INTER, MONO, glowGreen } from "../theme";

// SCENE — THE MOAT, v3 (Ahmed: the green-vs-red checkmark grid was weak — clichéd + redundant with the
// exploit scene). New frame: the FALSE TRADE-OFF. Credit each camp's REAL strength (builds credibility,
// not a rigged scorecard), name its fatal flaw, then land ACR-QA as the synthesis that pays neither tax.
// All verified: Snyk/Semgrep recall 14.9/17.6% → miss ~80%; GPT-5.5 ~$62 + non-deterministic; ACR-QA $0.
const Check = () => <span style={{ color: C.green, fontWeight: 700 }}>✓</span>;
const Cross = () => <span style={{ color: C.red, fontWeight: 700 }}>✗</span>;

const Row: React.FC<{
  appearAt: number;
  name: string;
  parts: React.ReactNode;
  hero?: boolean;
}> = ({ appearAt, name, parts, hero }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = frame < appearAt ? 0 : spring({ frame: frame - appearAt, fps, config: { mass: 1, damping: 26, stiffness: 150 } });
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        width: 942,
        height: hero ? 112 : 92,
        padding: "0 30px",
        borderRadius: 14,
        border: `1px solid ${hero ? "rgba(34,197,94,0.5)" : C.border}`,
        background: hero ? "rgba(34,197,94,0.07)" : "rgba(255,255,255,0.015)",
        opacity: s,
        transform: `translateY(${(1 - s) * 14}px) scale(${hero ? 0.96 + s * 0.04 : 1})`,
        boxShadow: hero ? "0 0 40px rgba(34,197,94,0.18)" : "none",
        gap: 22,
      }}
    >
      <span
        style={{
          fontFamily: MONO,
          fontSize: hero ? 34 : 27,
          fontWeight: 700,
          color: hero ? C.green : C.white,
          minWidth: 250,
          ...(hero ? glowGreen(18) : {}),
        }}
      >
        {name}
      </span>
      <span style={{ fontFamily: INTER, fontSize: hero ? 30 : 26, fontWeight: 500, color: hero ? C.white : C.muted }}>
        {parts}
      </span>
    </div>
  );
};

export const Moat: React.FC = () => {
  const frame = useCurrentFrame();
  const title = interpolate(frame, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const kicker = interpolate(frame, [150, 168], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "absolute", top: 104, width: "100%", textAlign: "center", opacity: title }}>
        <span style={{ fontFamily: INTER, fontSize: 42, fontWeight: 600, color: C.white }}>
          Every other tool makes you <span style={{ color: C.muted }}>trade off.</span>
        </span>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 20, marginTop: 36 }}>
        <Row
          appearAt={22}
          name="Snyk · Semgrep"
          parts={
            <>
              free <Check /> &nbsp;·&nbsp; but miss ~80% of real bugs <Cross />
            </>
          }
        />
        <Row
          appearAt={58}
          name="GPT-5.5 agents"
          parts={
            <>
              accurate <Check /> &nbsp;·&nbsp; but ~$62/scan &amp; never the same twice <Cross />
            </>
          }
        />
        <Row
          appearAt={100}
          hero
          name="ACR-QA"
          parts={
            <>
              $0 <Check /> &nbsp;·&nbsp; deterministic <Check /> &nbsp;·&nbsp; proves it <Check />
            </>
          }
        />
      </div>

      <div style={{ position: "absolute", bottom: 100, width: "100%", textAlign: "center", opacity: kicker }}>
        <span style={{ fontFamily: INTER, fontSize: 44, fontWeight: 700, color: C.white }}>
          So I <span style={{ color: C.green, ...glowGreen(20) }}>didn&apos;t.</span>
        </span>
      </div>
    </AbsoluteFill>
  );
};
