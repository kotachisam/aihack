"""Type definitions for AI model integrations."""

from typing import Any, Dict, Optional, Protocol

from .common import AnalysisResult, CodeText, TaskName


class AIModel(Protocol):
    """Protocol defining the interface for AI models."""

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate response from model."""
        ...

    async def code_review(self, code: CodeText, task: TaskName) -> AnalysisResult:
        """Review code for specified task."""
        ...

    async def analyze_code(self, code: CodeText) -> AnalysisResult:
        """Analyze code structure and provide insights."""
        ...

    async def is_available(self) -> bool:
        """Check if model is available."""
        ...


class ModelResponse:
    """Structured response from AI model."""

    def __init__(
        self,
        content: str,
        model: str,
        task: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.content = content
        self.model = model
        self.task = task
        self.metadata = metadata or {}


# Model configuration types
OllamaConfig = Dict[str, Any]
ClaudeConfig = Dict[str, Any]
GeminiConfig = Dict[str, Any]
