import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C, INTER, glowGreen } from "../theme";
import { Punch } from "../components/Kinetic";

// SCENE 1 — HOOK. The contrarian pattern-interrupt (research: number-shock alone fails — 58.2 vs 58.8
// is illegible cold; the *win must be named*). Cold-open arrests in < 3s on the reversal, then names a
// legible win (beats GPT-5.5, $0). "AI" reads to the mixed feed; the body clarifies "no LLM in the verdict".
export const Hook: React.FC = () => {
  const frame = useCurrentFrame();

  // Beat 1 — the enemy. Present from frame 0 (tiny ease, no hard pop).
  const l1 = interpolate(frame, [0, 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // Beat 1 dims as the turn lands, so the eye goes to the reversal.
  const l1dim = interpolate(frame, [40, 56], [1, 0.4], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 80 }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 46%, rgba(0,0,0,0.55) 30%, transparent 72%)" }} />

      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 26, textAlign: "center" }}>
        {/* Beat 1 — the enemy */}
        <div style={{ opacity: l1 * l1dim }}>
          <span style={{ fontFamily: INTER, fontSize: 48, fontWeight: 500, color: C.muted, lineHeight: 1.3 }}>
            Everyone is wiring{" "}
            <span style={{ color: C.white, fontWeight: 600 }}>LLMs</span> into security scanners.
          </span>
        </div>

        {/* Beat 2 — the reversal (the pattern interrupt) */}
        <Punch appearAt={42} from={0.62}>
          <span
            style={{
              fontFamily: INTER,
              fontSize: 92,
              fontWeight: 800,
              letterSpacing: "-0.02em",
              color: C.white,
              lineHeight: 1.05,
            }}
          >
            I <span style={{ color: C.green, ...glowGreen(44) }}>ripped mine out.</span>
          </span>
        </Punch>

        {/* Beat 3 — the legible win */}
        <Punch appearAt={86} from={0.7}>
          <span style={{ fontFamily: INTER, fontSize: 46, fontWeight: 600, color: C.white, lineHeight: 1.35 }}>
            It still out-recalls GPT-5.5 — at{" "}
            <span style={{ color: C.green, ...glowGreen(26) }}>$0.</span>
          </span>
        </Punch>
      </div>
    </AbsoluteFill>
  );
};
