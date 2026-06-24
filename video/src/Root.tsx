import { Composition } from "remotion";
import { MainComposition } from "./acrqa/Composition";

// ACR-QA — 90-second cinematic LinkedIn video. 1080×1080 · 30fps · 2700 frames · NO audio.
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ACR-QA"
      component={MainComposition}
      durationInFrames={2700}
      fps={30}
      width={1080}
      height={1080}
    />
  );
};
