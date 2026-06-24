import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, INTER, MONO, SPRING_ENDCARD, glowGreen, glowWhite } from "../theme";

const El: React.FC<{ appearAt: number; children: React.ReactNode }> = ({ appearAt, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  if (frame < appearAt) return null;
  const s = spring({ frame: frame - appearAt, fps, config: SPRING_ENDCARD });
  return <div style={{ opacity: s, transform: `translateY(${(1 - s) * 14}px)` }}>{children}</div>;
};

// FINAL SCENE — confident product close (Ahmed: the two-lane "ENGINEERS / HIRING" CTA read needy).
// The work carries the authority; the LinkedIn post copy carries the ask. Availability is stated once,
// as a fact, not a plea. Held ~12s static so the repo URL is readable without scrubbing.
export const EndCard: React.FC = () => {
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill
        style={{ background: "radial-gradient(ellipse 72% 64% at 50% 50%, rgba(0,0,0,0.55) 28%, transparent 80%)" }}
      />
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 20, textAlign: "center" }}>
        <El appearAt={6}>
          <span style={{ fontFamily: MONO, fontSize: 96, fontWeight: 700, letterSpacing: "-0.03em", color: C.white, ...glowWhite(32) }}>
            ACR-QA
          </span>
        </El>
        <El appearAt={26}>
          <span style={{ fontFamily: INTER, fontSize: 34, fontWeight: 600, color: C.green, ...glowGreen(24) }}>
            No LLM — it out-recalls the ones that have one.
          </span>
        </El>

        <El appearAt={52}>
          <div style={{ width: 540, height: 1, backgroundColor: C.border, margin: "14px 0" }} />
        </El>

        <El appearAt={64}>
          <span style={{ fontFamily: INTER, fontSize: 32, fontWeight: 500, color: C.white }}>
            Free &amp; open source · built solo in 9 months
          </span>
        </El>
        <El appearAt={92}>
          <span style={{ fontFamily: MONO, fontSize: 34, color: C.white, marginTop: 4, ...glowWhite(14) }}>
            github.com/ahmed-145/ACR-QA
          </span>
        </El>
        <El appearAt={124}>
          <span style={{ fontFamily: INTER, fontSize: 23, fontWeight: 500, letterSpacing: "0.04em", color: C.muted, marginTop: 12 }}>
            Ahmed Abbas · KSIU · open to backend · DevOps · SWE roles
          </span>
        </El>
      </div>
    </AbsoluteFill>
  );
};
