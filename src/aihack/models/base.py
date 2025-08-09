"""Base model interface and protocols for AI-Hack."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from ..types.common import AnalysisResult, CodeText, TaskName


class TrustLevel(Enum):
    """Model trust levels for security classification."""

    VERIFIED_LOCAL = 1  # CodeLlama, Mixtral, Gemma, StarCoder
    EXPERIMENTAL_LOCAL = 2  # DeepSeek, Qwen, custom fine-tunes
    CLOUD = 3  # Claude, GPT-4, Gemini
    UNKNOWN = 4  # User-added models


class ModelCapability(Enum):
    """Capabilities that models can support."""

    CODE_REVIEW = "code_review"
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    REFACTORING = "refactoring"


@dataclass
class ModelMetadata:
    """Metadata describing a model's properties and capabilities."""

    name: str
    provider: str  # "ollama", "anthropic", "google", "custom"
    trust_level: TrustLevel
    capabilities: List[ModelCapability]
    max_context_tokens: int
    cost_per_1k_tokens: float  # 0 for local models
    avg_response_time_ms: Optional[int] = None
    quality_score: Optional[float] = None  # 0-1 rating based on benchmarks


@dataclass
class ModelResponse:
    """Structured response from any AI model."""

    content: str
    model_name: str
    task: str
    response_time_ms: int
    metadata: Dict[str, Any]


class BaseModel(Protocol):
    """Protocol that all AI models must implement."""

    metadata: ModelMetadata

    async def code_review(self, code: CodeText, task: TaskName) -> AnalysisResult:
        """Review code for specified task with optimized prompts."""
        ...

    async def analyze_code(self, code: CodeText) -> AnalysisResult:
        """Analyze code structure and provide insights."""
        ...

    async def is_available(self) -> bool:
        """Check if model is available and responsive."""
        ...

    async def health_check(self) -> Dict[str, Any]:
        """Detailed health and performance status."""
        ...


class ModelError(Exception):
    """Base exception for model-related errors."""

    def __init__(
        self, message: str, model_name: str, cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.model_name = model_name
        self.cause = cause


class ModelUnavailableError(ModelError):
    """Raised when a model is not available or not responding."""

    pass


class ModelTimeoutError(ModelError):
    """Raised when a model request times out."""

    pass


class ModelRateLimitError(ModelError):
    """Raised when API rate limits are exceeded."""

    pass
