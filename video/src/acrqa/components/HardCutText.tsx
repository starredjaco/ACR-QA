import { useCurrentFrame } from "remotion";

// Text on an EXACT frame, zero easing. Renders children only inside [appearAt, until).
export const HardCut: React.FC<{
  appearAt: number;
  until?: number;
  children: React.ReactNode;
}> = ({ appearAt, until = Infinity, children }) => {
  const frame = useCurrentFrame();
  if (frame < appearAt || frame >= until) return null;
  return <>{children}</>;
};
