"""Centralized task registry for AI-Hack - single source of truth."""

from typing import Any, Dict, List

from ..types.prompts import TaskType


class TaskRegistry:
    """Central registry for task configuration and validation."""

    @classmethod
    def get_all_task_names(cls) -> List[str]:
        """Get list of all valid task names."""
        return [task.value for task in TaskType]

    @classmethod
    def is_valid_task(cls, task_name: str) -> bool:
        """Check if task name is valid."""
        return task_name.lower() in cls.get_all_task_names()

    @classmethod
    def get_task_config(cls, task_name: str) -> Dict[str, Any]:
        """Get configuration for a specific task."""
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
            task_name,
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
