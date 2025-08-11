import time
from typing import Any, Dict

from anthropic import APIStatusError, AsyncAnthropic
from anthropic.types import TextBlock

from ..types.common import AnalysisResult, CodeText, TaskName
from .base import ModelCapability, ModelError, ModelMetadata, TrustLevel


class ClaudeModel:
    """Claude AI model implementation with BaseModel interface."""

    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.metadata = ModelMetadata(
            name="claude-3.5-sonnet",
            provider="anthropic",
            trust_level=TrustLevel.CLOUD,
            capabilities=[
                ModelCapability.CODE_REVIEW,
                ModelCapability.CODE_ANALYSIS,
                ModelCapability.CODE_GENERATION,
                ModelCapability.SECURITY_ANALYSIS,
                ModelCapability.REFACTORING,
            ],
            max_context_tokens=200000,
            cost_per_1k_tokens=0.015,  # Approximate Claude pricing
            avg_response_time_ms=2000,
        )

    async def code_review(self, code: CodeText, task: TaskName) -> AnalysisResult:
        """Review code using Claude with cloud-optimized prompts."""
        system_prompt = self._get_cloud_system_prompt(task)
        user_prompt = self._format_user_prompt(code, task)

        try:
            message = await self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
            )

            if not message.content:
                raise ModelError(
                    "Received empty response from Claude", self.metadata.name
                )

            content_block = message.content[0]
            if isinstance(content_block, TextBlock):
                return str(content_block.text)
            else:
                raise ModelError(
                    f"Received unexpected content block type: {type(content_block)}",
                    self.metadata.name,
                )

        except APIStatusError as e:
            raise ModelError(
                f"Claude API status error: {e.status_code} - {e.response}",
                self.metadata.name,
                e,
            )
        except Exception as e:
            raise ModelError(f"Claude API error: {str(e)}", self.metadata.name, e)

    async def analyze_code(self, code: CodeText) -> AnalysisResult:
        """Analyze code structure using Claude's comprehensive capabilities."""
        return await self.code_review(code, "analyze")

    async def generate(self, prompt: str) -> str:
        """Generate a response to a general prompt using Claude."""
        system_prompt = (
            "You are an AI coding assistant. Focus on software development, programming, "
            "and technical topics. When you see 'LLM' assume it means Large Language Model, "
            "not legal terms. Provide concise, practical responses focused on code, "
            "development workflows, and technical problem-solving."
        )

        try:
            message = await self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            if not message.content:
                raise ModelError(
                    "Received empty response from Claude", self.metadata.name
                )

            content_block = message.content[0]
            if isinstance(content_block, TextBlock):
                return str(content_block.text)
            else:
                raise ModelError(
                    f"Received unexpected content block type: {type(content_block)}",
                    self.metadata.name,
                )

        except APIStatusError as e:
            raise ModelError(
                f"Claude API status error: {e.status_code} - {e.response}",
                self.metadata.name,
                e,
            )
        except Exception as e:
            raise ModelError(f"Claude API error: {str(e)}", self.metadata.name, e)

    async def is_available(self) -> bool:
        """Check if Claude API is available."""
        try:
            await self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except APIStatusError:
            return False
        except Exception:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Detailed Claude API health status."""
        start_time = time.time()

        try:
            await self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=10,
                messages=[{"role": "user", "content": "health check"}],
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
        """Get comprehensive system prompts optimized for Claude's capabilities."""
        prompts = {
            "review": (
                "You are an expert software engineer providing comprehensive code review. "
                "Analyze the code for type safety, error handling, performance, security, "
                "and maintainability. Provide actionable feedback with specific examples "
                "and concrete improvement suggestions. Be thorough but concise."
            ),
            "analyze": (
                "You are a senior software architect analyzing code structure and design. "
                "Examine the architecture, design patterns, dependencies, and overall "
                "organization. Identify strengths and areas for improvement. Consider "
                "both current implementation and future maintainability."
            ),
            "security": (
                "You are a security expert conducting a thorough security review. "
                "Look for vulnerabilities including: input validation issues, injection "
                "risks, authentication/authorization flaws, data exposure, and insecure "
                "coding practices. Rate severity and provide specific remediation steps."
            ),
        }
        return prompts.get(task, prompts["analyze"])

    def _format_user_prompt(self, code: CodeText, task: TaskName) -> str:
        """Format user prompt for Claude with proper context."""
        return f"Please {task} this Python code:\n\n```python\n{code}\n```"
