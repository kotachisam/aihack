"""Centralized task registry for AI-Hack - single source of truth."""

from typing import Any, Dict, List

from ..types.prompts import TaskType


class TaskRegistry:
    """Central registry for task configuration and validation."""

    # Task aliases mapping - maps alternative spellings to canonical task names
    TASK_ALIASES = {
        "analyse": "analyze",  # GB spelling
        "optimise": "optimize",  # GB spelling
        "colour": "color",  # GB spelling (if we add color task later)
        "favour": "favor",  # GB spelling (if we add favor task later)
    }

    @classmethod
    def get_all_task_names(cls) -> List[str]:
        """Get list of all valid task names."""
        return [task.value for task in TaskType]

    @classmethod
    def resolve_task_alias(cls, task_name: str) -> str:
        """Resolve task alias to canonical task name."""
        task_name_lower = task_name.lower()
        return cls.TASK_ALIASES.get(task_name_lower, task_name_lower)

    @classmethod
    def is_valid_task(cls, task_name: str) -> bool:
        """Check if task name is valid (including aliases)."""
        resolved_task = cls.resolve_task_alias(task_name)
        return resolved_task in cls.get_all_task_names()

    @classmethod
    def get_task_config(cls, task_name: str) -> Dict[str, Any]:
        """Get configuration for a specific task (resolves aliases)."""
        resolved_task = cls.resolve_task_alias(task_name)
        configs = {
            TaskType.ANALYZE.value: {
                "description": "Analyze code structure and organization",
                "prompt_style": "structured",
                "expected_output": "4-aspect analysis",
            },
            TaskType.REVIEW.value: {
                "description": "Review code for issues and improvements",
                "prompt_style": "ultra_tight",
                "expected_output": "issue/fix/priority format",
            },
            TaskType.SECURITY.value: {
                "description": "Scan for security vulnerabilities",
                "prompt_style": "tight",
                "expected_output": "vulnerability detection",
            },
            TaskType.REFACTOR.value: {
                "description": "Suggest code refactoring improvements",
                "prompt_style": "structured",
                "expected_output": "refactoring suggestions",
            },
            TaskType.OPTIMIZE.value: {
                "description": "Identify performance optimization opportunities",
                "prompt_style": "structured",
                "expected_output": "performance improvements",
            },
            TaskType.DEBUG.value: {
                "description": "Help debug code issues and errors",
                "prompt_style": "tight",
                "expected_output": "debugging assistance",
            },
        }

        return configs.get(
            resolved_task,
            {
                "description": "Unknown task",
                "prompt_style": "structured",
                "expected_output": "analysis",
            },
        )

    @classmethod
    def get_default_task(cls) -> str:
        """Get default task if none specified."""
        return TaskType.ANALYZE.value
