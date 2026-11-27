<h1 align="center">
  <img src="web/brand/favicon.svg" alt="FrameForge Logo" width="84" height="84" />
  <br />
  FrameForge
</h1>

<p align="center">
  <strong>Self-Hosted Autonomous Video Creation, Remotion Composition &amp; Multi-Platform Studio</strong>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python" /></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/Backend-FastAPI%20%2B%20SQLAlchemy-009688?style=flat-square&amp;logo=fastapi&amp;logoColor=white" alt="FastAPI" /></a>
  <a href="https://www.remotion.dev/"><img src="https://img.shields.io/badge/Renderer-Remotion%20%2B%20FFmpeg-0EA5E9?style=flat-square" alt="Remotion" /></a>
  <a href="https://github.com/k2-fsa/sherpa-onnx"><img src="https://img.shields.io/badge/ASR-Parakeet%200.6B%20(sherpa--onnx)-8B5CF6?style=flat-square" alt="ASR" /></a>
  <br />
  <a href="https://github.com/ushalabs/FrameForge"><img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-111208?style=flat-square" alt="Platform" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License" /></a>
</p>

---

## About FrameForge

**FrameForge** is a local-first, self-hosted video creation and clipping studio. Alongside its clip-extraction and live-stream highlight tools, FrameForge reconstructs **original, narrated videos** from authorized source material using frame extraction, AI research & scripting, local narration & subtitle alignment, deterministic **Remotion** rendering, and mandatory human approval before publishing.

It supports:

- **Unified source ingestion (`studio/sources/`)**: Hardened URL validation (SSRF, private IP, and path-traversal protection) with adapters for direct media URLs, local files, and `yt-dlp` sources.
- **Frame extraction & asset catalog (`studio/assets/`)**: Scene-balanced, scene-change, or uniform `ffmpeg` sampling with black/blur filtering, perceptual dHash deduplication, contact sheets, and honest shortfall reporting.
- **Visual intelligence & scripting (`studio/creation/`)**: Transcript alignment, semantic asset retrieval, injection-resistant original script generation, and verified-asset storyboarding.
- **Narration & timing (`studio/narration/`)**: Pluggable local TTS interface with deterministic fallback synthesis, `loudnorm` audio normalization, word-level alignment, and strictly monotonic caption cues.
- **Responsive Remotion composition (`renderer/`)**: TypeScript/React Remotion workspace supporting `9:16`, `16:9`, `1:1`, and `4:5` aspect ratios with safe-area padding and `ffprobe` quality gates.
- **Human review & safe publishing**: Every generated project enters `pending_review`, requiring explicit approval and source-rights confirmation before an idempotent publish can proceed.
- **Niche discovery & autonomous batches (`studio/discovery/`, `studio/autonomy/`)**: Channel presets, topic deduplication ledger, and daily-capped batch creation.
- **Classic clipping & live recording**: Full support for VOD clipping, Parakeet 0.6B local ASR, framing layouts (`blur`, `zoom`, `crop`, `gameplay`, `split`), and YouTube/Instagram/TikTok publishing.

---

## Desktop App

Run FrameForge as a native desktop window (with the classic system tray icon):

```bash
pip install -r requirements-desktop.txt
cd renderer && npm install && cd ..
python -m studio.desktop
```

Or double-click `Start-ClipForge-Windows.bat` (Windows) / `Start-ClipForge-Mac.command` (macOS).

To build a standalone desktop bundle:

```bash
python scripts/build-desktop.py
```

To build a Windows NSIS installer:

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_setup.ps1
```

For browser/server mode instead of the desktop window, run `python -m studio.server` (or set `FRAMEFORGE_BROWSER_ONLY=1`).

---

## Configuration & Environment

FrameForge reads `FRAMEFORGE_*` environment variables first and falls back to `CLIPFORGE_*` for backwards compatibility:

- `FRAMEFORGE_DATA`: Persistent data directory (videos, extracted assets, projects, database).
- `FRAMEFORGE_PORT`: HTTP server port (default `8765`).
- `FRAMEFORGE_ACCOUNTS`: Set to `1` to enable multi-user sign-in, Google OAuth, and the admin dashboard.

### AI Providers

Configure your AI provider in the dashboard (**Settings → AI**) or via `.env`:

```ini
FRAMEFORGE_AI_PROVIDER=gemini
FRAMEFORGE_AI_MODELS=gemini-2.5-flash
FRAMEFORGE_AI_KEY=your-api-key
```

| Provider ID | Service | Notes |
|---|---|---|
| `gemini` | Google Gemini | Native JSON schema support |
| `openai` | OpenAI | Chat Completions JSON mode |
| `xai` | xAI (Grok) | OpenAI-compatible |
| `groq` | Groq | Fast hosted inference |
| `openrouter` | OpenRouter | Multi-model routing |
| `anthropic` | Anthropic (Claude) | Native Messages API |
| `ollama` | Ollama | Local inference, no API key required |
| `custom` | Custom OpenAI-compatible | Set `FRAMEFORGE_AI_BASE_URL` |

Multiple comma-separated model IDs are tried in order as automatic fallbacks.

---

## Verification

Run the FrameForge module & end-to-end tests:

```bash
python -m unittest tests/test_desktop.py tests/test_sources.py tests/test_assets.py tests/test_research.py tests/test_creation.py tests/test_narration.py tests/test_render_pipeline.py tests/test_publish_gate.py tests/test_discovery.py tests/test_autonomy.py -v
python -m unittest tests/test_projects_api.py -v
python -m unittest tests/test_e2e_pipeline.py -v
```

See [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for architecture and deployment details.

---

## License

Released under the [MIT License](LICENSE).
