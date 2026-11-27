# FrameForge Deployment & Operations Guide

## Environment Variables

FrameForge reads `FRAMEFORGE_*` settings first and falls back to `CLIPFORGE_*` for backwards compatibility:

- `FRAMEFORGE_DATA`: Path to persistent data directory (videos, extracted assets, projects, database).
- `FRAMEFORGE_PORT`: HTTP server port (default `8765`).
- `FRAMEFORGE_ACCOUNTS`: Set to `1` on multi-user or public deployments to require sign-in.

## Running Locally

```bash
python -m studio.server
```

## Backups

Back up `FRAMEFORGE_DATA` (or `data/` and `storage.json`) regularly. All project manifests, asset catalogs, and publish ledgers live under `FRAMEFORGE_DATA/projects/`.

## Verification

Run the FrameForge module test suites:

```bash
python -m unittest tests/test_sources.py tests/test_assets.py tests/test_research.py tests/test_creation.py tests/test_narration.py tests/test_render_pipeline.py tests/test_projects_api.py tests/test_publish_gate.py tests/test_discovery.py tests/test_autonomy.py -v
```
