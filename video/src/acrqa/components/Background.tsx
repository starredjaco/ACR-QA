import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C } from "../theme";
import { seeded } from "./Kinetic";

// Slow-drifting foreground motes — constant, subtle ambient motion + parallax depth (no new focal point).
const Motes: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <>
      {Array.from({ length: 18 }, (_, i) => {
        const speed = 0.25 + seeded(i) * 0.5;
        const y = (1120 - ((frame * speed + seeded(i + 7) * 1120) % 1180)) - 30;
        const x = seeded(i + 3) * 1080 + Math.sin((frame / 90) + i) * 18;
        const size = 2 + seeded(i + 11) * 3.5;
        const op = (0.1 + seeded(i + 5) * 0.22) * (i % 5 === 0 ? 1 : 0.7);
        const green = i % 4 === 0;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: size,
              height: size,
              borderRadius: "50%",
              backgroundColor: green ? C.green : "#ffffff",
              opacity: op,
            }}
          />
        );
      })}
    </>
  );
};

// Persistent living background — drifting grid + two soft orbiting glows + a slow scan line + vignette.
// Rendered once behind the whole video so nothing is ever "bare black".
export const Background: React.FC<{ tint?: "green" | "blue" | "neutral" }> = ({ tint = "neutral" }) => {
  const frame = useCurrentFrame();

  const gridShift = (frame * 0.25) % 56;

  // two big blurred glows drifting in slow orbits
  const gx = 540 + Math.cos(frame / 220) * 260;
  const gy = 420 + Math.sin(frame / 260) * 220;
  const bx = 540 + Math.cos(frame / 300 + 2) * 300;
  const by = 640 + Math.sin(frame / 240 + 1) * 240;
  const glowPulse = 0.08 + 0.03 * Math.sin(frame / 70);

  const greenOpacity = tint === "blue" ? 0.05 : glowPulse;
  const blueOpacity = tint === "green" ? 0.05 : glowPulse * 0.8;

  // scan line sweeps top→bottom every ~6s
  const scanY = interpolate(frame % 200, [0, 200], [-40, 1120]);

  const farShift = (frame * 0.1) % 116; // slower → parallax depth behind the near grid

  return (
    <AbsoluteFill style={{ backgroundColor: "#070708", overflow: "hidden" }}>
      {/* far grid plane (slow → depth) */}
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(#101012 1px, transparent 1px), linear-gradient(90deg, #101012 1px, transparent 1px)`,
          backgroundSize: "116px 116px",
          backgroundPosition: `${farShift}px ${-farShift}px`,
          opacity: 0.5,
        }}
      />
      {/* near grid plane (faster → foreground) */}
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${C.border} 1px, transparent 1px), linear-gradient(90deg, ${C.border} 1px, transparent 1px)`,
          backgroundSize: "56px 56px",
          backgroundPosition: `${gridShift}px ${gridShift}px`,
          opacity: 0.4,
        }}
      />
      {/* green glow */}
      <div
        style={{
          position: "absolute",
          left: gx - 360,
          top: gy - 360,
          width: 720,
          height: 720,
          borderRadius: "50%",
          background: `radial-gradient(circle, rgba(34,197,94,${greenOpacity}) 0%, transparent 65%)`,
          filter: "blur(40px)",
        }}
      />
      {/* blue glow */}
      <div
        style={{
          position: "absolute",
          left: bx - 380,
          top: by - 380,
          width: 760,
          height: 760,
          borderRadius: "50%",
          background: `radial-gradient(circle, rgba(59,130,246,${blueOpacity}) 0%, transparent 65%)`,
          filter: "blur(50px)",
        }}
      />
      {/* slow scan line */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: scanY,
          width: "100%",
          height: 2,
          background: "linear-gradient(90deg, transparent, rgba(34,197,94,0.18), transparent)",
        }}
      />
      {/* drifting ambient motes */}
      <Motes />
      {/* vignette */}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(circle at 50% 45%, transparent 45%, rgba(0,0,0,0.55) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};
