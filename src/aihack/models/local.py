import time
from typing import Any, Dict

import httpx

from ..prompts.analyze.local_structured import (
    ANALYZE_STRUCTURED_SYSTEM,
    ANALYZE_STRUCTURED_USER,
)
from ..prompts.review.local_ultra_tight import (
    REVIEW_ULTRA_TIGHT_SYSTEM,
    REVIEW_ULTRA_TIGHT_USER,
)
from ..prompts.security.local_tight import SECURITY_TIGHT_SYSTEM, SECURITY_TIGHT_USER
from ..types.common import AnalysisResult, CodeText, TaskName
from .base import ModelCapability, ModelError, ModelMetadata, TrustLevel


class OllamaModel:
    """Local AI model integration via Ollama with BaseModel interface."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "codellama:7b-instruct",
    ) -> None:
        self.base_url = base_url
        self.model_name = model_name
        self.client = httpx.AsyncClient(base_url=base_url)
        self.metadata = ModelMetadata(
            name=model_name,
            provider="ollama",
            trust_level=TrustLevel.VERIFIED_LOCAL,
            capabilities=[
                ModelCapability.CODE_REVIEW,
                ModelCapability.CODE_ANALYSIS,
                ModelCapability.SECURITY_ANALYSIS,
                ModelCapability.REFACTORING,
            ],
            max_context_tokens=4096,  # CodeLlama 7B context window
            cost_per_1k_tokens=0.0,  # Local models are free
            avg_response_time_ms=7000,  # Based on our testing
        )

    async def generate(self, prompt: str, model: str | None = None) -> str:
        """Generate response from local model"""
        if model is None:
            model = self.model_name

        try:
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Lower temperature for code tasks
                        "top_p": 0.9,
                    },
                },
                timeout=30.0,
            )
            result = response.json()
            response_text: str = result.get("response", "")
            return response_text
        except Exception as e:
            raise ModelError(f"Ollama API error: {str(e)}", self.metadata.name, e)

    async def code_review(self, code: CodeText, task: TaskName) -> AnalysisResult:
        """Review code using ultra-tight prompts to eliminate hallucinations"""
        task_lower = task.lower()

        if task_lower == "review":
            system_prompt = REVIEW_ULTRA_TIGHT_SYSTEM
            user_prompt = REVIEW_ULTRA_TIGHT_USER.format(code=code)
        elif task_lower == "analyze":
            system_prompt = ANALYZE_STRUCTURED_SYSTEM
            user_prompt = ANALYZE_STRUCTURED_USER.format(language="python", code=code)
        elif task_lower == "security":
            system_prompt = SECURITY_TIGHT_SYSTEM
            user_prompt = SECURITY_TIGHT_USER.format(code=code)
        else:
            # Default to review for unknown tasks
            system_prompt = REVIEW_ULTRA_TIGHT_SYSTEM
            user_prompt = REVIEW_ULTRA_TIGHT_USER.format(code=code)

        # Combine system and user prompts for local models
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        return await self.generate(full_prompt)

    async def analyze_code(self, code: CodeText) -> AnalysisResult:
        """Analyze code structure using structured prompts"""
        system_prompt = ANALYZE_STRUCTURED_SYSTEM
        user_prompt = ANALYZE_STRUCTURED_USER.format(language="python", code=code)

        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        return await self.generate(full_prompt)

    async def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = await self.client.get("/api/tags", timeout=5.0)
            return bool(response.status_code == 200)
        except Exception:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Detailed Ollama health status."""
        start_time = time.time()

        try:
            response = await self.client.get("/api/tags", timeout=5.0)
            response_time = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                tags = response.json()
                return {
                    "available": True,
                    "response_time_ms": response_time,
                    "model": self.metadata.name,
                    "status": "healthy",
                    "available_models": [
                        model.get("name", "") for model in tags.get("models", [])
                    ],
                }
            else:
                return {
                    "available": False,
                    "error": f"HTTP {response.status_code}",
                    "model": self.metadata.name,
                    "status": "unhealthy",
                }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "model": self.metadata.name,
                "status": "unhealthy",
            }
