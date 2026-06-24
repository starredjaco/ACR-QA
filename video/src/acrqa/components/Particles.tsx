import { useCurrentFrame } from "remotion";
import { C } from "../theme";
import { seeded } from "./Kinetic";

const GATES = [292, 470, 650]; // y of the three filter gates (matches the funnel arrows)

// Living funnel flow: green "survivor" particles stream down the centre and visibly thin out at each
// gate; red "noise" particles burst outward at every gate. Visualises 1,942 → 55 filtering.
export const FunnelFlow: React.FC = () => {
  const frame = useCurrentFrame();

  const green = Array.from({ length: 34 }, (_, i) => {
    const phase = (frame * 2.1 + seeded(i) * 660) % 660;
    const y = 150 + phase;
    const surv = seeded(i + 50);
    const threshold = y < GATES[0] ? 0 : y < GATES[1] ? 0.32 : y < GATES[2] ? 0.62 : 0.9;
    const op = surv > threshold ? 0.6 : 0;
    const x = 540 + (seeded(i + 200) - 0.5) * 70;
    const size = 5 + seeded(i + 9) * 4;
    return { x, y, op, size };
  });

  const red: { x: number; y: number; op: number }[] = [];
  GATES.forEach((gy, gi) => {
    for (let k = 0; k < 7; k++) {
      const id = gi * 17 + k;
      const t = (frame * 0.9 + seeded(id) * 46) % 46; // 0..46 lifecycle
      const side = seeded(id + 3) > 0.5 ? 1 : -1;
      const x = 540 + side * (24 + t * 9.5);
      const y = gy + (seeded(id + 7) - 0.5) * 18 + t * 0.4;
      const op = Math.max(0, (1 - t / 46)) * 0.7;
      red.push({ x, y, op });
    }
  });

  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      {green.map((d, i) =>
        d.op > 0 ? (
          <div
            key={`g${i}`}
            style={{
              position: "absolute",
              left: d.x,
              top: d.y,
              width: d.size,
              height: d.size,
              borderRadius: "50%",
              backgroundColor: C.green,
              opacity: d.op,
              boxShadow: `0 0 8px rgba(34,197,94,0.7)`,
            }}
          />
        ) : null,
      )}
      {red.map((d, i) => (
        <div
          key={`r${i}`}
          style={{
            position: "absolute",
            left: d.x,
            top: d.y,
            width: 6,
            height: 6,
            borderRadius: "50%",
            backgroundColor: C.red,
            opacity: d.op,
          }}
        />
      ))}
    </div>
  );
};
