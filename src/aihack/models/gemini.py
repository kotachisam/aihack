import asyncio
import time
from typing import Any, Dict

import google.generativeai as genai

from ..types.common import AnalysisResult, CodeText, TaskName
from .base import ModelCapability, ModelError, ModelMetadata, TrustLevel


class GeminiModel:
    """Google Gemini AI model implementation with BaseModel interface."""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        self.metadata = ModelMetadata(
            name="gemini-pro",
            provider="google",
            trust_level=TrustLevel.CLOUD,
            capabilities=[
                ModelCapability.CODE_REVIEW,
                ModelCapability.CODE_ANALYSIS,
                ModelCapability.CODE_GENERATION,
                ModelCapability.PERFORMANCE_OPTIMIZATION,
                ModelCapability.REFACTORING,
            ],
            max_context_tokens=1000000,  # Gemini's large context window
            cost_per_1k_tokens=0.001,  # Approximate Gemini pricing
            avg_response_time_ms=1500,
        )

    async def code_review(self, code: CodeText, task: TaskName) -> AnalysisResult:
        """Review code using Gemini with cloud-optimized prompts."""
        system_prompt = self._get_cloud_system_prompt(task)
        user_prompt = self._format_user_prompt(code, task)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            # Gemini doesn't have native async, so we wrap in executor
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content(full_prompt)
            )

            response_text: str = response.text
            return response_text

        except Exception as e:
            raise ModelError(f"Gemini API error: {str(e)}", self.metadata.name, e)

    async def analyze_code(self, code: CodeText) -> AnalysisResult:
        """Analyze code structure using Gemini's comprehensive capabilities."""
        return await self.code_review(code, "analyze")

    async def is_available(self) -> bool:
        """Check if Gemini API is available."""
        try:
            test_response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content("test")
            )
            return test_response is not None
        except Exception:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Detailed Gemini API health status."""
        start_time = time.time()

        try:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.model.generate_content("health check")
            )

            response_time = int((time.time() - start_time) * 1000)
            return {
                "available": True,
                "response_time_ms": response_time,
                "model": self.metadata.name,
                "status": "healthy",
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "model": self.metadata.name,
                "status": "unhealthy",
            }

    def _get_cloud_system_prompt(self, task: TaskName) -> str:
        """Get comprehensive system prompts optimized for Gemini's capabilities."""
        prompts = {
            "review": (
                "You are an expert software engineer providing comprehensive code review. "
                "Focus on code quality, performance, maintainability, and best practices. "
                "Provide specific, actionable feedback with concrete examples."
            ),
            "analyze": (
                "You are a senior software architect analyzing code structure. "
                "Examine the design patterns, architecture, and organization. "
                "Consider scalability, maintainability, and potential improvements."
            ),
            "security": (
                "You are a security expert conducting security analysis. "
                "Look for vulnerabilities, security anti-patterns, and potential "
                "attack vectors. Provide severity ratings and remediation steps."
            ),
            "optimize": (
                "You are a performance optimization expert. "
                "Analyze the code for performance bottlenecks, inefficient algorithms, "
                "and optimization opportunities. Provide specific improvements."
            ),
        }
        return prompts.get(task, prompts["analyze"])

    def _format_user_prompt(self, code: CodeText, task: TaskName) -> str:
        """Format user prompt for Gemini with proper context."""
        return f"Please {task} this Python code:\n\n```python\n{code}\n```"
