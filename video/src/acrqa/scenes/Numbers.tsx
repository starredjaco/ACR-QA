import { AbsoluteFill, useCurrentFrame } from "remotion";
import { C, MONO, glowGreen, glowWhite } from "../theme";
import { Breathe, CountUp, Punch } from "../components/Kinetic";

// SCENE — THE RIGOR FLASH. Two clean engineering numbers (Ahmed: "9 months / 1 person" was redundant —
// the solo note lives once on the end card now). Reinforces the engineering/backend story.
const W = { fontFamily: MONO, color: C.white, ...glowWhite(16) } as const;

export const Numbers: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill
        style={{ background: "radial-gradient(ellipse 64% 50% at 50% 50%, rgba(0,0,0,0.4) 0%, transparent 78%)" }}
      />
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 22, textAlign: "center" }}>
        {frame >= 30 ? (
          <span style={{ ...W, fontSize: 76 }}>
            <CountUp to={3147} appearAt={30} dur={26} /> tests.
          </span>
        ) : null}
        {frame >= 90 ? (
          <Punch appearAt={90} from={0.5}>
            <Breathe amp={0.03} period={60}>
              <span
                style={{
                  fontFamily: MONO,
                  fontSize: 100,
                  fontWeight: 700,
                  letterSpacing: "-0.04em",
                  color: C.green,
                  ...glowGreen(54),
                }}
              >
                88% coverage.
              </span>
            </Breathe>
          </Punch>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
