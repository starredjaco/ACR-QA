import { C, MONO } from "../theme";

const Dot: React.FC<{ color: string }> = ({ color }) => (
  <div style={{ width: 13, height: 13, borderRadius: "50%", backgroundColor: color }} />
);

// Reusable terminal shell: dark border, header bar with three dots, optional title.
export const Terminal: React.FC<{
  width: number;
  height: number;
  title?: string;
  titleColor?: string;
  bg?: string;
  children: React.ReactNode;
}> = ({ width, height, title, titleColor = C.blue, bg = "#000000", children }) => {
  return (
    <div
      style={{
        width,
        height,
        border: `1px solid ${C.border}`,
        borderRadius: 12,
        backgroundColor: bg,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          height: 48,
          backgroundColor: C.border,
          display: "flex",
          alignItems: "center",
          paddingLeft: 20,
          gap: 10,
          flexShrink: 0,
        }}
      >
        <Dot color={C.red} />
        <Dot color="#eab308" />
        <Dot color={C.green} />
        {title ? (
          <span style={{ fontFamily: MONO, color: titleColor, fontSize: 24, marginLeft: 22 }}>
            {title}
          </span>
        ) : null}
      </div>
      <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>{children}</div>
    </div>
  );
};
