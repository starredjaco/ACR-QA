import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { C, INTER } from "../theme";

// SCENE — THE TURN (research beat 8). A deliberate near-black "visual silence" that resets the
// viewer before the human/creator reveal. Its own opaque dark fill covers the living background.
export const Turn: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [10, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  // imperceptible continuous push-in — nothing is ever perfectly still
  const scale = interpolate(frame, [0, 90], [1, 1.04]);
  const blur = interpolate(frame, [10, 32], [10, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: "#070708", justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          fontFamily: INTER,
          fontSize: 56,
          fontWeight: 500,
          letterSpacing: "-0.01em",
          color: C.white,
          opacity,
          scale,
          filter: `blur(${blur}px)`,
        }}
      >
        Built entirely from scratch.
      </div>
    </AbsoluteFill>
  );
};
