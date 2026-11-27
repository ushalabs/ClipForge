import React from "react";
import { Composition } from "remotion";
import { FrameForgeVideo } from "./compositions/FrameForgeVideo.tsx";
import { ASPECT_PRESETS, type RenderManifest } from "./types.ts";

const defaultManifest: RenderManifest = {
  project_id: "preview",
  title: "FrameForge Preview",
  aspect_ratio: "9:16",
  fps: 30,
  scenes: [{ scene_id: "scene_01", asset_path: "", duration_sec: 5 }],
  captions: [{ index: 1, start_sec: 0, end_sec: 3, text: "FrameForge Preview" }],
};

export const RemotionRoot: React.FC = () => {
  const preset = ASPECT_PRESETS[defaultManifest.aspect_ratio];
  return (
    <Composition
      id="FrameForgeVideo"
      component={FrameForgeVideo}
      durationInFrames={150}
      fps={defaultManifest.fps}
      width={preset.width}
      height={preset.height}
      defaultProps={defaultManifest}
    />
  );
};
