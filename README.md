<h1 align="center">
  <img src="web/brand/favicon.svg" alt="ClipForge Logo" width="84" height="84" />
  <br />
  ClipForge
</h1>

<p align="center">
  <strong>Self-Hosted AI Video Clipping, Live Stream Highlights &amp; Multi-Platform Publishing</strong>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python" /></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/Backend-FastAPI%20%2B%20SQLAlchemy-009688?style=flat-square&amp;logo=fastapi&amp;logoColor=white" alt="FastAPI" /></a>
  <a href="https://ffmpeg.org/"><img src="https://img.shields.io/badge/Media-FFmpeg%20%2B%20yt--dlp-007808?style=flat-square&amp;logo=ffmpeg&amp;logoColor=white" alt="FFmpeg" /></a>
  <a href="https://github.com/k2-fsa/sherpa-onnx"><img src="https://img.shields.io/badge/ASR-Parakeet%200.6B%20(sherpa--onnx)-8B5CF6?style=flat-square" alt="ASR" /></a>
  <br />
  <a href="https://github.com/ushalabs/ClipForge"><img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-111208?style=flat-square" alt="Platform" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License" /></a>
</p>

---

## About ClipForge

**ClipForge** is a local-first, self-hosted clipping studio that turns long-form videos and live streams into captioned vertical clips ready for YouTube Shorts, Instagram Reels, and TikTok.

It supports:

- **VOD & channel ingestion** from YouTube, Twitch, Kick, playlists, or local file uploads
- **Word-level local transcription** using Parakeet 0.6B via `sherpa-onnx` (or a remote GPU ASR worker)
- **AI-assisted highlight selection** using timestamped transcripts, audio loudness spikes, chat activity, and YouTube retention peaks
- **Automated 9:16 rendering** with word-by-word ASS captions (`Bounce`, `Hype`, `Clean`), hooks, and multiple framing layouts (`blur`, `zoom`, `crop`, `gameplay`, `split`)
- **Live stream clipping** from rolling buffers while a broadcast is still running
- **Creator workspaces & scheduled publishing** to YouTube, Instagram, and TikTok with daily caps and spacing
- **Optional multi-user mode** (`CLIPFORGE_ACCOUNTS=1`) with email/password auth, Google OAuth, and an admin dashboard

---

## Features

### Clip Discovery & Transcription
- **Fast YouTube discovery** using existing YouTube transcripts (`CLIPFORGE_YT_TRANSCRIPT=1`) before running local ASR only on selected clips
- **Most-Replayed & chapter awareness** to surface high-retention moments even on calm talking-head or podcast videos
- **Channel & playlist batching** plus automatic RSS polling for newly published YouTube uploads
- **Loudness fallback** so clipping still works without an AI key

### Vertical Rendering & Layouts
- **Five framing modes**: blurred fill (`blur`), zoomed fill (`zoom`), centre crop (`crop`), automatic corner facecam detection (`gameplay`), and top/bottom speaker split (`split`)
- **Three bundled caption styles** (`Bounce`, `Hype`, `Clean`) rendered with `Poppins ExtraBold`, `Anton`, and `Archivo Black`
- **Hinglish / Romanization support** for Hindi and Urdu speech

### YouTube, Instagram & TikTok Publishing
- **One-click OAuth connections** for YouTube, Instagram, and TikTok
- **Creator-level posting rules**: minimum score threshold, post spacing, daily caps, native YouTube `publishAt` scheduling, source-video linking, and non-Shorts 16:9 support
- **Post analytics**: tracks views, likes, and comments for published clips

---

## AI Providers

Configure your AI provider in the dashboard (**Settings → AI**) or via `.env`:

```ini
CLIPFORGE_AI_PROVIDER=gemini
CLIPFORGE_AI_MODELS=gemini-2.5-flash
CLIPFORGE_AI_KEY=your-api-key
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
| `custom` | Custom OpenAI-compatible | Set `CLIPFORGE_AI_BASE_URL` |

Multiple comma-separated model IDs are tried in order as automatic fallbacks.

---

## License

Released under the [MIT License](LICENSE).
