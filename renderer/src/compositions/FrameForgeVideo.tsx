import React from "react";
import { AbsoluteFill, Audio, Img, Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { ASPECT_PRESETS, type RenderManifest } from "../types.ts";

export const FrameForgeVideo: React.FC<RenderManifest> = ({
  aspect_ratio,
  audio_path,
  scenes,
  captions,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const preset = ASPECT_PRESETS[aspect_ratio] ?? ASPECT_PRESETS["9:16"];
  const currentSec = frame / fps;

  const activeCue = captions.find(
    (c) => currentSec >= c.start_sec && currentSec < c.end_sec,
  );

  let cursorFrames = 0;
  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0f14" }}>
      {audio_path ? <Audio src={audio_path} /> : null}

      {scenes.map((scene) => {
        const from = cursorFrames;
        const durationInFrames = Math.max(1, Math.round(scene.duration_sec * fps));
        cursorFrames += durationInFrames;
        return (
          <Sequence key={scene.scene_id} from={from} durationInFrames={durationInFrames}>
            <AbsoluteFill>
              <Img
                src={scene.asset_path}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {activeCue ? (
        <AbsoluteFill
          style={{
            justifyContent: "flex-end",
            alignItems: "center",
            paddingLeft: preset.safePaddingX,
            paddingRight: preset.safePaddingX,
            paddingBottom: preset.safePaddingY,
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              backgroundColor: "rgba(11, 15, 20, 0.78)",
              color: "#f4f7fb",
              fontSize: Math.round(preset.width * 0.044),
              fontWeight: 700,
              lineHeight: 1.25,
              textAlign: "center",
              padding: "14px 24px",
              borderRadius: 12,
              maxWidth: "90%",
            }}
          >
            {activeCue.text}
          </div>
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
