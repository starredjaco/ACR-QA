import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, INTER, MONO, glowGreen } from "../theme";
import { Terminal } from "../components/Terminal";

// SCENE — THE SCAN (the "money shot"). A faithful, SMOOTH live scan of dvpwa, styled like the real
// dashboard: spinner→check tool rows, severity pills, attestation badges, a real finding card.
const TOOLS = ["bandit", "semgrep", "ruff", "taint", "exploit"];
const ROW_AT = (i: number) => 26 + i * 17;
const TOOLS_DONE = ROW_AT(TOOLS.length - 1) + 26;

const ToolRow: React.FC<{ name: string; appearAt: number }> = ({ name, appearAt }) => {
  const frame = useCurrentFrame();
  const reveal = interpolate(frame, [appearAt - 8, appearAt + 4], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const fill = interpolate(frame, [appearAt, appearAt + 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const done = fill > 0.99;
  // spinner while running
  const spin = interpolate(frame % 30, [0, 30], [0, 360]);
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        height: 50,
        opacity: reveal,
        transform: `translateX(${(1 - reveal) * -16}px)`,
        fontFamily: MONO,
        fontSize: 27,
      }}
    >
      <div style={{ width: 36, display: "flex", justifyContent: "center" }}>
        {done ? (
          <span style={{ color: C.green, fontSize: 26 }}>✓</span>
        ) : (
          <div
            style={{
              width: 18,
              height: 18,
              borderRadius: "50%",
              border: `2px solid rgba(59,130,246,0.25)`,
              borderTopColor: C.blue,
              transform: `rotate(${spin}deg)`,
            }}
          />
        )}
      </div>
      <div style={{ width: 180, color: done ? C.white : C.muted }}>{name}</div>
      <div style={{ width: 440, height: 12, borderRadius: 6, backgroundColor: "rgba(255,255,255,0.06)", overflow: "hidden" }}>
        <div
          style={{
            width: `${fill * 100}%`,
            height: "100%",
            background: done ? C.green : C.blue,
            boxShadow: done ? "0 0 10px rgba(34,197,94,0.5)" : "none",
          }}
        />
      </div>
    </div>
  );
};

const Pill: React.FC<{ appearAt: number; n: number; label: string; fg: string; bg: string }> = ({ appearAt, n, label, fg, bg }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = frame < appearAt ? 0 : spring({ frame: frame - appearAt, fps, config: { mass: 1, damping: 24, stiffness: 160 } });
  return (
    <span
      style={{
        fontFamily: MONO,
        fontSize: 28,
        fontWeight: 700,
        color: fg,
        background: bg,
        borderRadius: 8,
        padding: "6px 16px",
        opacity: s,
        transform: `scale(${0.85 + s * 0.15})`,
      }}
    >
      {n} {label}
    </span>
  );
};

const Badge: React.FC<{ appearAt: number; text: string }> = ({ appearAt, text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = frame < appearAt ? 0 : spring({ frame: frame - appearAt, fps, config: { mass: 1, damping: 24, stiffness: 160 } });
  return (
    <span
      style={{
        fontFamily: MONO,
        fontSize: 22,
        color: C.green,
        border: `1px solid rgba(34,197,94,0.35)`,
        borderRadius: 6,
        padding: "5px 12px",
        opacity: s,
      }}
    >
      ✓ {text}
    </span>
  );
};

export const Scan: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const total = Math.round(
    interpolate(frame, [TOOLS_DONE, TOOLS_DONE + 16], [0, 32], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
  );
  const cardAt = TOOLS_DONE + 60;
  const cardS = frame < cardAt ? 0 : spring({ frame: frame - cardAt, fps, config: { mass: 1, damping: 22, stiffness: 150 } });
  const capOp = interpolate(frame, [cardAt + 16, cardAt + 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // Dynamic focus (research: auto-zoom the eye to the result). The whole terminal pushes in toward
  // the finding card as it lands, so the SQL-injection line is the unambiguous focal point.
  const focusZoom = interpolate(frame, [cardAt, cardAt + 40], [1, 1.09], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const focusY = interpolate(frame, [cardAt, cardAt + 40], [0, -54], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // "Live" signals: a blinking cursor + an elapsed timer ticking up to a real 3.8s, freezing on done.
  const blink = (frame % 30) < 15;
  const elapsed = interpolate(frame, [10, TOOLS_DONE], [0, 3.8], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const running = frame < TOOLS_DONE;

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ transform: `translateY(${focusY}px) scale(${focusZoom})`, transformOrigin: "center 72%" }}>
      <Terminal width={1000} height={716} title="ACR-QA · live scan" titleColor={C.green} bg={C.terminalBg}>
        <div style={{ padding: "28px 36px", fontFamily: MONO }}>
          <div style={{ fontSize: 27, color: C.white, marginBottom: 14, display: "flex", alignItems: "baseline" }}>
            <span style={{ color: C.green }}>$</span>
            <span style={{ marginLeft: 10 }}>acrqa scan</span>
            <span style={{ color: C.blue, marginLeft: 9 }}>github.com/anxolerd/dvpwa</span>
            {/* blinking block cursor — nothing on screen is ever frozen */}
            <span style={{ marginLeft: 4, color: C.white, opacity: blink ? 0.9 : 0, fontWeight: 700 }}>▋</span>
            <span style={{ flex: 1 }} />
            <span style={{ fontSize: 22, color: running ? C.blue : C.muted }}>
              {running ? "scanning… " : "done in "}
              {elapsed.toFixed(1)}s
            </span>
          </div>

          {TOOLS.map((t, i) => (
            <ToolRow key={t} name={t} appearAt={ROW_AT(i)} />
          ))}

          {/* results: count + severity pills (real dashboard look) */}
          <div style={{ marginTop: 22, display: "flex", alignItems: "center", gap: 16, opacity: frame >= TOOLS_DONE ? 1 : 0 }}>
            <span style={{ fontFamily: MONO, fontSize: 40, fontWeight: 700, color: C.white }}>{total} findings</span>
            <Pill appearAt={TOOLS_DONE + 10} n={13} label="HIGH" fg="#fca5a5" bg="rgba(239,68,68,0.16)" />
            <Pill appearAt={TOOLS_DONE + 18} n={12} label="MED" fg="#fcd34d" bg="rgba(245,158,11,0.16)" />
            <Pill appearAt={TOOLS_DONE + 26} n={7} label="LOW" fg="#cbd5e1" bg="rgba(148,163,184,0.14)" />
          </div>

          <div style={{ marginTop: 18, display: "flex", gap: 14 }}>
            <Badge appearAt={TOOLS_DONE + 20} text="ECDSA-P256" />
            <Badge appearAt={TOOLS_DONE + 30} text="Dilithium3 PQ" />
            <Badge appearAt={TOOLS_DONE + 40} text="Rekor logged" />
          </div>

          {/* the finding card */}
          <div
            style={{
              marginTop: 24,
              borderRadius: 10,
              border: `1px solid rgba(239,68,68,0.35)`,
              background: "rgba(239,68,68,0.06)",
              padding: "16px 20px",
              opacity: cardS,
              transform: `translateY(${(1 - cardS) * 20}px)`,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 14, fontFamily: MONO, fontSize: 28 }}>
              <span style={{ color: "#fca5a5", background: "rgba(239,68,68,0.16)", borderRadius: 6, padding: "2px 12px", fontWeight: 700 }}>
                HIGH
              </span>
              <span style={{ color: C.white }}>SQL injection</span>
              <span style={{ color: C.muted }}>sqli/dao/student.py:42</span>
            </div>
            <div style={{ fontFamily: MONO, fontSize: 23, color: C.muted, marginTop: 10 }}>
              {"q = \"INSERT INTO students … '%(name)s'\" % {'name': "}
              <span style={{ color: "#fca5a5" }}>name</span>
              {"}"}
            </div>
          </div>
        </div>
      </Terminal>
      </div>

      <div style={{ position: "absolute", bottom: 56, width: "100%", textAlign: "center", opacity: capOp }}>
        <span style={{ fontFamily: INTER, fontSize: 36, fontWeight: 600, color: C.white }}>
          1,942 raw → <span style={{ color: C.green, ...glowGreen(18) }}>55 confirmed.</span> No LLM in the verdict.
        </span>
      </div>
    </AbsoluteFill>
  );
};
