"""Type definitions for prompt system."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple


class TaskType(Enum):
    """All supported task types."""

    ANALYZE = "analyze"
    REVIEW = "review"
    SECURITY = "security"
    REFACTOR = "refactor"
    OPTIMIZE = "optimize"
    DEBUG = "debug"


class ModelType(Enum):
    """Model categories with different prompt needs."""

    LOCAL = "local"
    CLOUD = "cloud"


class PromptStyle(Enum):
    """Different prompt constraint levels."""

    ULTRA_TIGHT = "ultra_tight"
    STRICT = "strict"
    STRUCTURED = "structured"
    COMPREHENSIVE = "comprehensive"


@dataclass
class PromptTemplate:
    """Template for generating optimized prompts."""

    system_prompt: str
    user_template: str
    constraints: Dict[str, Any]


# Prompt function types
PromptPair = Tuple[str, str]  # (system_prompt, user_prompt)
PromptFormatter = callable  # Function that formats prompts
PromptValidator = callable  # Function that validates prompts
