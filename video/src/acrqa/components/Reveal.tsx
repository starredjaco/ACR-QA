import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// Cinematic entrance: opacity + slide-up + blur-resolve. Smoother than a hard "appear".
export const Reveal: React.FC<{
  appearAt: number;
  y?: number;
  blur?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ appearAt, y = 26, blur = 12, children, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s =
    frame < appearAt
      ? 0
      : spring({ frame: frame - appearAt, fps, config: { mass: 0.7, damping: 16, stiffness: 90 } });
  return (
    <div
      style={{
        opacity: s,
        transform: `translateY(${(1 - s) * y}px)`,
        filter: `blur(${(1 - s) * blur}px)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

// Fades a scene's content in over the first `inLen` frames and out over the last `outLen` frames,
// so scenes dissolve through the living background instead of hard-cutting.
export const SceneFade: React.FC<{
  durationInFrames: number;
  inLen?: number;
  outLen?: number;
  dir?: number; // pan direction: +1 enters from right, -1 from left
  children: React.ReactNode;
}> = ({ durationInFrames, inLen = 18, outLen = 18, dir = 1, children }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [0, inLen, durationInFrames - outLen, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  // seamless pan in/out — camera move across a canvas, not a hard cut
  const x = interpolate(
    frame,
    [0, inLen, durationInFrames - outLen, durationInFrames],
    [dir * 60, 0, 0, -dir * 60],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  // CONTINUOUS slow push-in across the whole hold — nothing is ever frozen (kills the "static" feel).
  const scale = interpolate(
    frame,
    [0, inLen, durationInFrames - outLen, durationInFrames],
    [1.05, 1.0, 1.055, 1.075],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  return (
    <div
      style={{
        opacity,
        width: "100%",
        height: "100%",
        transform: `translateX(${x}px) scale(${scale})`,
        transformOrigin: "center",
      }}
    >
      {children}
    </div>
  );
};
