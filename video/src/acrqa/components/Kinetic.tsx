import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// Deterministic seeded RNG (no Math.random) → stable particle fields.
export function seeded(i: number) {
  const x = Math.sin(i * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

// A number that counts up to `to` over `dur` frames starting at `appearAt`.
export const CountUp: React.FC<{
  to: number;
  appearAt: number;
  dur?: number;
  style?: React.CSSProperties;
}> = ({ to, appearAt, dur = 34, style }) => {
  const frame = useCurrentFrame();
  const e = interpolate(frame, [appearAt, appearAt + dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const eased = 1 - Math.pow(1 - e, 3); // ease-out cubic
  const v = Math.round(eased * to);
  return <span style={style}>{v.toLocaleString()}</span>;
};

// Continuous "breathing" — subtle scale + glow oscillation. Keeps hero elements alive.
export const Breathe: React.FC<{
  children: React.ReactNode;
  amp?: number;
  period?: number;
  style?: React.CSSProperties;
}> = ({ children, amp = 0.018, period = 70, style }) => {
  const frame = useCurrentFrame();
  const s = 1 + amp * Math.sin((frame / period) * Math.PI * 2);
  return <div style={{ transform: `scale(${s})`, ...style }}>{children}</div>;
};

// Punch-in entrance: fast scale-in that DECELERATES and settles — no overshoot/bounce
// (research: elastic bounce reads as amateur). Critically-damped for a clean "impact".
export const Punch: React.FC<{
  appearAt: number;
  children: React.ReactNode;
  from?: number;
  style?: React.CSSProperties;
}> = ({ appearAt, children, from = 0.6, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s =
    frame < appearAt ? 0 : spring({ frame: frame - appearAt, fps, config: { mass: 1, damping: 26, stiffness: 170 } });
  const scale = from + (1 - from) * s;
  return (
    <div style={{ opacity: Math.min(1, s * 1.5), transform: `scale(${scale})`, ...style }}>
      {children}
    </div>
  );
};
