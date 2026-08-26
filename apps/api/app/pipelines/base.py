from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class VisionPipeline(ABC):
    """Base class for all vision pipelines."""

    @abstractmethod
    def preprocess(self, frame: Any) -> Any:
        """Preprocess the input frame."""
        pass

    @abstractmethod
    def infer(self, frame: Any, model: Any, **kwargs) -> Any:
        """Run inference using the model."""
        pass

    @abstractmethod
    def postprocess(self, result: Any) -> Any:
        """Post-process inference results."""
        pass

    @abstractmethod
    def track(self, result: Any) -> Any:
        """Apply tracking to the results."""
        pass

    @abstractmethod
    def create_events(self, result: Any, context: Dict = None) -> List[Dict]:
        """Generate events from the results."""
        pass

    @abstractmethod
    def format_result(self, result: Any) -> Dict:
        """Format the final result for output."""
        pass