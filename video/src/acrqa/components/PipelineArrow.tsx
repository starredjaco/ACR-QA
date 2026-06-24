import { interpolate, useCurrentFrame } from "remotion";

// A downward arrow that "draws itself" over [drawStart, drawEnd] via stroke-dashoffset.
export const PipelineArrow: React.FC<{
  drawStart: number;
  drawEnd: number;
  height: number; // pixel length of the shaft
  color: string;
}> = ({ drawStart, drawEnd, height, color }) => {
  const frame = useCurrentFrame();
  if (frame < drawStart) return null;

  const progress = interpolate(frame, [drawStart, drawEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const shaft = height - 16; // leave room for the head
  const headOpacity = interpolate(progress, [0.8, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <svg width={40} height={height} style={{ display: "block" }}>
      <line
        x1={20}
        y1={0}
        x2={20}
        y2={shaft}
        stroke={color}
        strokeWidth={3}
        strokeDasharray={shaft}
        strokeDashoffset={shaft * (1 - progress)}
      />
      <polygon
        points={`10,${shaft} 30,${shaft} 20,${height}`}
        fill={color}
        opacity={headOpacity}
      />
    </svg>
  );
};
