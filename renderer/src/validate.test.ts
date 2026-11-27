import assert from "node:assert/strict";
import { validateManifest } from "./validate.ts";
import type { RenderManifest } from "./types.ts";

const validManifest: RenderManifest = {
  project_id: "proj_1",
  title: "Test Video",
  aspect_ratio: "9:16",
  fps: 30,
  scenes: [{ scene_id: "scene_01", asset_path: "frames/asset_0001.jpg", duration_sec: 4.0 }],
  captions: [{ index: 1, start_sec: 0.0, end_sec: 2.0, text: "Hello world" }],
};

assert.deepEqual(validateManifest(validManifest), []);

const badManifest: RenderManifest = {
  ...validManifest,
  scenes: [],
  captions: [
    { index: 1, start_sec: 0.0, end_sec: 2.0, text: "First" },
    { index: 2, start_sec: 1.5, end_sec: 3.0, text: "Overlap" },
  ],
};

const errors = validateManifest(badManifest);
assert.ok(errors.length >= 2, "Expected validation errors for empty scenes and overlapping captions");
console.log("renderer validate.test.ts: OK");
