"""Dynamic prompt loader for different task types and model configurations."""

from enum import Enum
from pathlib import Path
from typing import Tuple


class TaskType(Enum):
    """Supported task types."""

    REVIEW = "review"
    ANALYZE = "analyze"
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

    ULTRA_TIGHT = "ultra_tight"  # Maximum constraints, zero hallucinations
    STRICT = "strict"  # High constraints, focused output
    STRUCTURED = "structured"  # Organized output, moderate constraints
    COMPREHENSIVE = "comprehensive"  # Detailed analysis, minimal constraints


class PromptLoader:
    """Loads appropriate prompts based on task, model, and style."""

    def __init__(self) -> None:
        self.prompts_dir = Path(__file__).parent

    def load_prompt(
        self,
        task: TaskType,
        model_type: ModelType,
        style: PromptStyle = PromptStyle.STRICT,
    ) -> Tuple[str, str]:
        """Load system and user prompts for given configuration."""

        # Determine prompt file path
        task_dir = self.prompts_dir / task.value
        prompt_file = f"{model_type.value}_{style.value}.py"
        prompt_path = task_dir / prompt_file

        # Fallback strategy if specific combination doesn't exist
        if not prompt_path.exists():
            # Try with just model type
            fallback_file = f"{model_type.value}_strict.py"
            prompt_path = task_dir / fallback_file

            if not prompt_path.exists():
                # Ultimate fallback to analyze structured
                prompt_path = self.prompts_dir / "analyze" / "local_structured.py"

        return self._load_from_file(prompt_path)

    def _load_from_file(self, prompt_path: Path) -> Tuple[str, str]:
        """Load system and user prompts from Python file."""
        # Import the module dynamically
        spec = __import__(prompt_path.stem, globals())

        # Look for SYSTEM and USER constants (with various naming patterns)
        system_prompt = None
        user_prompt = None

        for attr_name in dir(spec):
            attr_value = getattr(spec, attr_name)
            if isinstance(attr_value, str):
                if "SYSTEM" in attr_name.upper():
                    system_prompt = attr_value
                elif "USER" in attr_name.upper():
                    user_prompt = attr_value

        if not system_prompt or not user_prompt:
            # Fallback to basic prompts
            system_prompt = "You are an AI assistant. Analyze the provided code."
            user_prompt = "Analyze this code:\n\n```python\n{code}\n```"

        return system_prompt, user_prompt

    def get_available_styles(
        self, task: TaskType, model_type: ModelType
    ) -> list[PromptStyle]:
        """Get available prompt styles for task/model combination."""
        task_dir = self.prompts_dir / task.value
        if not task_dir.exists():
            return [PromptStyle.STRICT]

        available = []
        prefix = f"{model_type.value}_"

        for file_path in task_dir.glob(f"{prefix}*.py"):
            style_name = file_path.stem.replace(prefix, "")
            try:
                style = PromptStyle(style_name)
                available.append(style)
            except ValueError:
                continue  # Skip invalid style names

        return available or [PromptStyle.STRICT]
