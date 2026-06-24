// ACR-QA video — design system (colors + fonts). Never deviate from these values.
import { loadFont as loadJetBrains } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";

// loadFont() at module scope makes Remotion block rendering until the font is ready.
export const MONO = loadJetBrains().fontFamily; // JetBrains Mono — all code, numbers, terminal, metrics
export const INTER = loadInter().fontFamily; // Inter — prose, narrative

export const C = {
  bg: "#0a0a0a",
  green: "#22c55e", // ACR-QA wins / confirmed
  blue: "#3b82f6", // gates, technical labels, tension
  red: "#ef4444", // noise, false positives
  white: "#ffffff",
  muted: "#6b7280",
  border: "#1a1a1a",
  terminalBg: "#0d1117",
} as const;

// Premium spring presets — HIGH damping, ZERO overshoot (research: bounce = amateur tell).
// Snappy entrance that decelerates and SETTLES, no elastic wobble.
export const SPRING_PREMIUM = { mass: 1, damping: 30, stiffness: 150 } as const; // entrances
export const SPRING_TIGHT = SPRING_PREMIUM;
export const SPRING_ENDCARD = { mass: 1, damping: 34, stiffness: 130 } as const;

// LAYERED glow (research: stack a tight bright halo + a wide faint bloom — simulates real lens
// dispersion; single high-opacity shadows look amateur).
export const glowGreen = (px = 30) => ({
  textShadow: `0 0 ${px * 0.6}px rgba(34,197,94,0.4), 0 0 ${px * 2.4}px rgba(34,197,94,0.12)`,
});
export const glowWhite = (px = 24) => ({
  textShadow: `0 0 ${px * 0.6}px rgba(255,255,255,0.28), 0 0 ${px * 2.2}px rgba(255,255,255,0.08)`,
});
export const glowBlue = (px = 22) => ({
  textShadow: `0 0 ${px * 0.6}px rgba(59,130,246,0.4), 0 0 ${px * 2.4}px rgba(59,130,246,0.12)`,
});
