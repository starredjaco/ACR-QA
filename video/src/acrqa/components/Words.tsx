import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { glowGreen } from "../theme";

// Kinetic typography: each word slides + blurs in on a stagger; emphasized words pop green + glow.
// This is the single biggest "it feels alive" upgrade for headline lines.
export const Words: React.FC<{
  text: string;
  appearAt: number;
  fontSize: number;
  color: string;
  stagger?: number;
  weight?: number;
  emphasis?: Record<string, string>; // bare word (no punctuation) -> color
  maxWidth?: number;
}> = ({ text, appearAt, fontSize, color, stagger = 3, weight = 400, emphasis = {}, maxWidth = 920 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = text.split(" ");
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        columnGap: "0.42em",
        rowGap: "0.18em",
        maxWidth,
        lineHeight: 1.32,
      }}
    >
      {words.map((w, i) => {
        const at = appearAt + i * stagger;
        const s =
          frame < at ? 0 : spring({ frame: frame - at, fps, config: { mass: 0.7, damping: 20, stiffness: 130 } });
        const bare = w.replace(/[.,!?]/g, "");
        const emp = emphasis[bare];
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              fontSize,
              fontWeight: emp ? 700 : weight,
              color: emp ?? color,
              opacity: s,
              transform: `translateY(${(1 - s) * 18}px)`,
              filter: `blur(${(1 - s) * 8}px)`,
              ...(emp ? glowGreen(22) : {}),
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};
