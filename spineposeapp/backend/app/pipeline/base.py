from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Keypoint:
    name: str
    x: float
    y: float
    confidence: float
    source_view: str
    x3d: float | None = None
    y3d: float | None = None
    z3d: float | None = None


class DetectorBase(ABC):
    """Abstract interface for pluggable pose detectors."""

    @abstractmethod
    def detect(self, frame_paths: dict[str, str]) -> dict:
        """Run detection on captured frame paths keyed by view name."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model name for logs and scan records."""
