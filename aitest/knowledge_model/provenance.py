"""
Provenance tracking — every metadata field knows which discovery source provided it.

Enables:
  - Agents to distinguish "observed by browser" from "parsed from source code"
  - Conflict detection when two sources disagree
  - Confidence scoring per field, not just overall

Usage:
    from aitest.knowledge_model.provenance import Source, Provenance, Confidence

    field = FieldValue(value="/system/user", provenance=[
        Provenance(source=Source.VUE_ROUTER, confidence=Confidence.HIGH, detail="router/index.ts:42"),
        Provenance(source=Source.BROWSER_USE, confidence=Confidence.HIGH, detail="sidebar scan"),
    ])
"""

from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Optional
import json


class Source(StrEnum):
    """Discovery source identifier."""
    BROWSER_USE = "browser-use"        # BrowserUse automation
    VUE_ROUTER = "vue-router"          # Vue 3 router/index.ts parsing
    VUE_COMPONENT = "vue-component"    # .vue SFC template analysis
    REACT_ROUTER = "react-router"      # React Router parsing
    OPENAPI = "openapi"                # OpenAPI/Swagger spec
    SWAGGER = "swagger"                # Swagger 2.0 spec
    MANUAL = "manual"                  # Human-provided
    INFERRED = "inferred"              # AI-inferred (LLM educated guess)
    MERGED = "merged"                  # Synthesized from multiple sources


class Confidence(Enum):
    """Confidence level for a metadata value."""
    CERTAIN = (1.0, "Multiple sources agree or verified")
    HIGH = (0.85, "Single reliable source (source code)")
    MEDIUM = (0.70, "Single observation (browser)")
    LOW = (0.50, "Inferred or single source with ambiguity")
    UNCERTAIN = (0.30, "LLM guess, unverified")

    def __init__(self, score: float, description: str):
        self.score = score
        self.description = description

    @classmethod
    def from_score(cls, score: float) -> "Confidence":
        for level in cls:
            if score >= level.score:
                return level
        return cls.UNCERTAIN


@dataclass
class Provenance:
    """
    Tracks where a metadata value came from and how confident we are.

    Multiple Provenance entries = multiple sources agree on the same value.
    """
    source: Source
    confidence: Confidence = Confidence.MEDIUM
    detail: str = ""          # e.g. "router/index.ts:42" or "sidebar scan pass #2"
    timestamp: str = ""       # ISO timestamp of discovery

    def to_dict(self) -> dict:
        return {
            "source": self.source.value,
            "confidence": self.confidence.score,
            "confidence_label": self.confidence.name,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Provenance":
        return cls(
            source=Source(d["source"]),
            confidence=Confidence.from_score(d.get("confidence", 0.5)),
            detail=d.get("detail", ""),
            timestamp=d.get("timestamp", ""),
        )


@dataclass
class FieldValue:
    """
    A metadata field with provenance tracking.

    value: the actual value
    provenance: list of sources that contributed this value
    """
    value: object
    provenance: list[Provenance] = field(default_factory=list)

    @property
    def confidence(self) -> float:
        """Aggregate confidence: max of all provenance entries, capped by agreement bonus."""
        if not self.provenance:
            return 0.0
        scores = [p.confidence.score for p in self.provenance]
        best = max(scores)
        # Bonus for multiple agreeing sources
        if len(set(p.source for p in self.provenance)) >= 2:
            best = min(1.0, best + 0.10)
        return best

    @property
    def sources(self) -> list[Source]:
        return [p.source for p in self.provenance]

    @property
    def primary_source(self) -> Optional[Source]:
        """Most reliable source for this value."""
        if not self.provenance:
            return None
        return max(self.provenance, key=lambda p: p.confidence.score).source

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "confidence": self.confidence,
            "provenance": [p.to_dict() for p in self.provenance],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FieldValue":
        return cls(
            value=d["value"],
            provenance=[Provenance.from_dict(p) for p in d.get("provenance", [])],
        )

    @classmethod
    def certain(cls, value: object, source: Source, detail: str = "") -> "FieldValue":
        """Shorthand: create a high-confidence field from a reliable source."""
        return cls(
            value=value,
            provenance=[Provenance(source=source, confidence=Confidence.CERTAIN, detail=detail)],
        )

    @classmethod
    def observed(cls, value: object, detail: str = "") -> "FieldValue":
        """Shorthand: create a browser-observed field."""
        return cls(
            value=value,
            provenance=[Provenance(source=Source.BROWSER_USE, confidence=Confidence.MEDIUM, detail=detail)],
        )

    @classmethod
    def inferred(cls, value: object, detail: str = "") -> "FieldValue":
        """Shorthand: create an LLM-inferred field."""
        return cls(
            value=value,
            provenance=[Provenance(source=Source.INFERRED, confidence=Confidence.LOW, detail=detail)],
        )


# ── Serialization helpers ────────────────────────────────────────────────

def serialize_field(fv: FieldValue) -> dict:
    """Serialize FieldValue for JSON output (used in .discovery/pages.json)."""
    return fv.to_dict()


def deserialize_field(d: dict) -> FieldValue:
    """Deserialize FieldValue from JSON input."""
    if isinstance(d, dict) and "provenance" in d:
        return FieldValue.from_dict(d)
    # Legacy format: plain value without provenance
    return FieldValue.inferred(d, "legacy data (no provenance)")


def serialize_optional(fv: Optional[FieldValue]) -> Optional[dict]:
    """Serialize optional FieldValue."""
    if fv is None:
        return None
    return fv.to_dict()


def deserialize_optional(d: Optional[dict]) -> Optional[FieldValue]:
    """Deserialize optional FieldValue."""
    if d is None:
        return None
    return deserialize_field(d)
