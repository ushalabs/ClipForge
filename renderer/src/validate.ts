import { ASPECT_PRESETS, type RenderManifest } from "./types.ts";

export function validateManifest(manifest: RenderManifest): string[] {
  const errors: string[] = [];
  if (!manifest || typeof manifest !== "object") {
    return ["Manifest must be an object."];
  }
  if (!manifest.project_id) {
    errors.push("project_id is required.");
  }
  if (!ASPECT_PRESETS[manifest.aspect_ratio]) {
    errors.push(`Unsupported aspect_ratio: ${String(manifest.aspect_ratio)}`);
  }
  if (!Number.isFinite(manifest.fps) || manifest.fps <= 0) {
    errors.push("fps must be a positive number.");
  }
  if (!Array.isArray(manifest.scenes) || manifest.scenes.length === 0) {
    errors.push("scenes must be a non-empty array.");
  } else {
    manifest.scenes.forEach((s, idx) => {
      if (!s.asset_path) errors.push(`scenes[${idx}].asset_path is required.`);
      if (!Number.isFinite(s.duration_sec) || s.duration_sec <= 0) {
        errors.push(`scenes[${idx}].duration_sec must be > 0.`);
      }
    });
  }
  if (Array.isArray(manifest.captions)) {
    let prevEnd = 0;
    manifest.captions.forEach((c, idx) => {
      if (c.end_sec <= c.start_sec) {
        errors.push(`captions[${idx}] end_sec must be > start_sec.`);
      }
      if (c.start_sec < prevEnd) {
        errors.push(`captions[${idx}] overlaps previous cue.`);
      }
      prevEnd = c.end_sec;
    });
  }
  return errors;
}
