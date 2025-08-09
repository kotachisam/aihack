"""Common type definitions used across AI-Hack."""

from typing import Any, Callable, Dict

# Basic types
TaskName = str
ModelName = str
PromptText = str
CodeText = str
FilePath = str

# Configuration types
Config = Dict[str, Any]
TaskConfig = Dict[str, Any]
ModelConfig = Dict[str, Any]

# Response types
AnalysisResult = str
ReviewResult = str
SecurityResult = str

# Function signature types
AsyncAnalysisFunction = Callable[[CodeText], str]
AsyncReviewFunction = Callable[[CodeText, TaskName], str]
