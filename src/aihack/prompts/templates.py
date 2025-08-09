"""Task-specific prompt templates optimized for different AI models."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class TaskType(Enum):
    """Supported task types for code analysis."""

    REVIEW = "review"
    ANALYZE = "analyze"
    REFACTOR = "refactor"
    OPTIMIZE = "optimize"
    SECURITY = "security"
    DEBUG = "debug"


class ModelType(Enum):
    """Supported model types with different prompt requirements."""

    LOCAL = "local"  # CodeLlama, Qwen2.5-Coder, etc.
    CLOUD = "cloud"  # Claude, Gemini


@dataclass
class PromptTemplate:
    """Template for generating optimized prompts."""

    system_prompt: str
    user_template: str
    constraints: Dict[str, Any]


class PromptTemplates:
    """Repository of optimized prompt templates."""

    # Local model templates (need more constraints and structure)
    _LOCAL_TEMPLATES = {
        TaskType.REVIEW: PromptTemplate(
            system_prompt=(
                "You are a Python code reviewer. Find these specific issues:\n"
                "1. Functions missing type hints (parameters and return types)\n"
                "2. Division operations without zero-checking\n"
                "3. Comparison using '!= None' instead of 'is not None'\n"
                "4. Missing docstrings on functions/classes\n"
                "5. Hardcoded secrets, SQL injection risks\n\n"
                "Examine the code carefully and identify ACTUAL problems.\n\n"
                "Format each issue found:\n"
                "Issue: [specific problem and line]\n"
                "Fix: [exact solution]\n"
                "Priority: HIGH/MEDIUM/LOW\n\n"
                "Maximum 3 most important issues."
            ),
            user_template="Review this {language} code:\n\n```{language}\n{code}\n```",
            constraints={"max_issues": 3, "format": "structured"},
        ),
        TaskType.ANALYZE: PromptTemplate(
            system_prompt=(
                "You are a code analysis expert. Analyze ONLY these aspects:\n"
                "1. Code structure and organization\n"
                "2. Dependencies and imports\n"
                "3. Main functionality and purpose\n"
                "4. Potential improvements\n\n"
                "Be factual and concise. Maximum 4 sentences per aspect."
            ),
            user_template="Analyze this {language} code:\n\n```{language}\n{code}\n```",
            constraints={"max_sentences_per_aspect": 4},
        ),
        TaskType.SECURITY: PromptTemplate(
            system_prompt=(
                "You are a security expert. Find ONLY security vulnerabilities:\n"
                "1. Input validation issues\n"
                "2. SQL injection risks\n"
                "3. XSS vulnerabilities\n"
                "4. Authentication/authorization flaws\n"
                "5. Data exposure risks\n\n"
                "For each vulnerability found:\n"
                "Vulnerability: [type and location]\n"
                "Risk Level: CRITICAL/HIGH/MEDIUM/LOW\n"
                "Fix: [specific remediation]\n\n"
                "If no vulnerabilities found, state 'No security issues detected.'"
            ),
            user_template="Security review of {language} code:\n\n```{language}\n{code}\n```",
            constraints={"focus": "security_only"},
        ),
    }

    # Cloud model templates (can handle more nuanced requests)
    _CLOUD_TEMPLATES = {
        TaskType.REVIEW: PromptTemplate(
            system_prompt=(
                "You are an expert software engineer providing comprehensive code review. "
                "Focus on code quality, maintainability, performance, and best practices. "
                "Provide actionable feedback with specific examples and suggestions."
            ),
            user_template=(
                "Please review this {language} code for quality, performance, and best practices:\n\n"
                "```{language}\n{code}\n```\n\n"
                "Consider: type safety, error handling, performance, security, and maintainability."
            ),
            constraints={"comprehensive": True},
        ),
        TaskType.ANALYZE: PromptTemplate(
            system_prompt=(
                "You are a senior software architect. Provide thoughtful analysis of code "
                "structure, design patterns, and architectural decisions. Consider both "
                "current implementation and potential improvements."
            ),
            user_template=(
                "Analyze this {language} code's architecture and design:\n\n"
                "```{language}\n{code}\n```\n\n"
                "Include: purpose, structure, patterns used, and improvement opportunities."
            ),
            constraints={"architectural_focus": True},
        ),
    }

    @classmethod
    def get_template(
        cls, task: TaskType, model_type: ModelType, language: str = "python"
    ) -> PromptTemplate:
        """Get optimized prompt template for task and model combination."""
        templates = (
            cls._LOCAL_TEMPLATES
            if model_type == ModelType.LOCAL
            else cls._CLOUD_TEMPLATES
        )

        template = templates.get(task)
        if not template:
            # Fallback to generic analyze template
            template = templates[TaskType.ANALYZE]

        return template

    @classmethod
    def format_prompt(
        cls,
        task: TaskType,
        model_type: ModelType,
        code: str,
        language: str = "python",
        **kwargs: Any,
    ) -> tuple[str, str]:
        """Format system and user prompts for the given task and model."""
        template = cls.get_template(task, model_type, language)

        # Format user prompt with code and language
        user_prompt = template.user_template.format(
            code=code, language=language, **kwargs
        )

        return template.system_prompt, user_prompt

    @classmethod
    def get_supported_tasks(cls) -> list[str]:
        """Get list of supported task types."""
        return [task.value for task in TaskType]
