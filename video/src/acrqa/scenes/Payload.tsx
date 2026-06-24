import { AbsoluteFill } from "remotion";
import { C, INTER, glowGreen, glowWhite } from "../theme";
import { HardCut } from "../components/HardCutText";
import { Punch } from "../components/Kinetic";

// SCENE — THE PAYLOAD (research beat 10). Rapid 1-second hard-cut keyword flashes. A burst of energy
// and pacing variation right before the quiet "turn". Each word snaps in big and hard-cuts to the next.
const WORDS: { text: string; green?: boolean }[] = [
  { text: "Deterministic." },
  { text: "Exploit-verified.", green: true },
  { text: "Signed." },
  { text: "Free.", green: true },
];

const Flash: React.FC<{ word: (typeof WORDS)[number]; appearAt: number }> = ({ word, appearAt }) => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
    <Punch appearAt={appearAt} from={0.6}>
      <span
        style={{
          fontFamily: INTER,
          fontSize: word.green ? 96 : 90,
          fontWeight: 800,
          letterSpacing: "-0.03em",
          color: word.green ? C.green : C.white,
          ...(word.green ? glowGreen(40) : glowWhite(26)),
        }}
      >
        {word.text}
      </span>
    </Punch>
  </AbsoluteFill>
);

export const Payload: React.FC = () => {
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <AbsoluteFill
        style={{ background: "radial-gradient(ellipse 70% 50% at 50% 50%, rgba(0,0,0,0.45) 0%, transparent 78%)" }}
      />
      {WORDS.map((w, i) => (
        <HardCut key={i} appearAt={i * 30} until={(i + 1) * 30}>
          <Flash word={w} appearAt={i * 30} />
        </HardCut>
      ))}
    </AbsoluteFill>
  );
};
