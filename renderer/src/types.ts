export type AspectRatio = "9:16" | "16:9" | "1:1" | "4:5";

export interface Dimensions {
  width: number;
  height: number;
  safePaddingX: number;
  safePaddingY: number;
}

export const ASPECT_PRESETS: Record<AspectRatio, Dimensions> = {
  "9:16": { width: 1080, height: 1920, safePaddingX: 72, safePaddingY: 160 },
  "16:9": { width: 1920, height: 1080, safePaddingX: 120, safePaddingY: 72 },
  "1:1": { width: 1080, height: 1080, safePaddingX: 72, safePaddingY: 72 },
  "4:5": { width: 1080, height: 1350, safePaddingX: 72, safePaddingY: 100 },
};

export interface CaptionCue {
  index: number;
  start_sec: number;
  end_sec: number;
  text: string;
}

export interface SceneItem {
  scene_id: string;
  asset_path: string;
  duration_sec: number;
  visual_cue?: string;
}

export interface RenderManifest {
  [key: string]: unknown;
  project_id: string;
  title: string;
  aspect_ratio: AspectRatio;
  fps: number;
  audio_path?: string;
  scenes: SceneItem[];
  captions: CaptionCue[];
}
