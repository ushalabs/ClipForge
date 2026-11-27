"""Visual intelligence, transcript alignment, source research, and semantic asset retrieval."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from studio.assets.catalog import AssetCatalog, AssetItem

_WORD_RE = re.compile(r"[a-z0-9]{2,}")


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall((text or "").lower()))


@dataclass
class EnrichedAsset:
    asset_id: str
    timestamp_sec: float
    transcript_context: str
    tags: list[str]
    quality_score: float
    rights_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchBrief:
    project_id: str
    topic: str
    summary: str
    claims: list[str] = field(default_factory=list)
    key_entities: list[str] = field(default_factory=list)
    enriched_assets: list[EnrichedAsset] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "topic": self.topic,
            "summary": self.summary,
            "claims": self.claims,
            "key_entities": self.key_entities,
            "enriched_assets": [a.to_dict() for a in self.enriched_assets],
        }


def align_transcript_to_assets(
    catalog: AssetCatalog,
    transcript_segments: list[dict[str, Any]] | None = None,
    window_sec: float = 4.0,
) -> list[EnrichedAsset]:
    """Attach nearby transcript text, tags, and a normalized quality score to each asset."""
    segments = transcript_segments or []
    enriched: list[EnrichedAsset] = []

    for item in catalog.assets:
        nearby_texts = []
        for seg in segments:
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start))
            if (start - window_sec) <= item.timestamp_sec <= (end + window_sec):
                txt = str(seg.get("text", "")).strip()
                if txt:
                    nearby_texts.append(txt)

        context = " ".join(nearby_texts).strip()
        tokens = sorted(_tokenize(context))
        tags = list(dict.fromkeys([*item.tags, *tokens[:8]]))
        # Quality score combines sharpness and balanced luma (avoiding too dark/bright).
        luma_balance = max(0.0, 1.0 - abs(item.mean_luma - 128.0) / 128.0)
        quality_score = round(min(1.0, (item.sharpness / 40.0) * 0.7 + luma_balance * 0.3), 4)

        enriched.append(
            EnrichedAsset(
                asset_id=item.asset_id,
                timestamp_sec=item.timestamp_sec,
                transcript_context=context,
                tags=tags,
                quality_score=quality_score,
                rights_status=item.rights_status,
            )
        )
    return enriched


def build_research_brief(
    catalog: AssetCatalog,
    topic: str,
    transcript_segments: list[dict[str, Any]] | None = None,
    claims: list[str] | None = None,
) -> ResearchBrief:
    """Build a structured research brief from source transcript and extracted assets."""
    segments = transcript_segments or []
    enriched = align_transcript_to_assets(catalog, segments)
    full_text = " ".join(str(s.get("text", "")).strip() for s in segments if s.get("text")).strip()
    summary = full_text[:400] if full_text else f"Visual research brief for {topic}."

    extracted_claims = list(claims or [])
    if not extracted_claims and full_text:
        sentences = [s.strip() for s in re.split(r"[.!?]+", full_text) if len(s.strip()) > 15]
        extracted_claims = sentences[:5]

    return ResearchBrief(
        project_id=catalog.project_id,
        topic=topic,
        summary=summary,
        claims=extracted_claims,
        key_entities=[],
        enriched_assets=enriched,
    )


def retrieve_assets(
    query: str,
    brief: ResearchBrief,
    top_k: int = 5,
) -> list[EnrichedAsset]:
    """Rank and return top-k assets matching `query` by tag/context overlap + quality."""
    q_tokens = _tokenize(query)
    scored: list[tuple[float, EnrichedAsset]] = []
    for asset in brief.enriched_assets:
        a_tokens = _tokenize(asset.transcript_context) | {t.lower() for t in asset.tags}
        overlap = len(q_tokens & a_tokens)
        score = overlap * 2.0 + asset.quality_score
        scored.append((score, asset))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [asset for _, asset in scored[: max(1, top_k)]]


def validate_asset_ids(asset_ids: list[str], catalog: AssetCatalog) -> list[str]:
    """Return any asset_ids that do not exist in `catalog` (empty list means all valid)."""
    valid = {a.asset_id for a in catalog.assets}
    return [aid for aid in asset_ids if aid not in valid]
