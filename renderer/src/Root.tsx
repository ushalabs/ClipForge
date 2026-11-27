import React from "react";
import { Composition, type CalculateMetadataFunction } from "remotion";
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

const calculateMetadata: CalculateMetadataFunction<RenderManifest> = ({ props }) => {
  const fps = props.fps || 30;
  const preset = ASPECT_PRESETS[props.aspect_ratio] ?? ASPECT_PRESETS["9:16"];
  const totalSec = (props.scenes || []).reduce(
    (sum, s) => sum + Math.max(0.5, Number(s.duration_sec) || 0.5),
    0,
  );
  return {
    durationInFrames: Math.max(1, Math.round(totalSec * fps)),
    fps,
    width: preset.width,
    height: preset.height,
  };
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
      calculateMetadata={calculateMetadata}
    />
  );
};
