"""Model management for AI model initialization, switching, and status."""
import asyncio
import subprocess
from typing import Any, Dict, Union

from ...config import Settings
from ...models.claude import ClaudeModel
from ...models.gemini import GeminiModel
from ...models.local import OllamaModel


class ModelManager:
    """Manages AI model initialization, switching, and availability."""

    def __init__(self) -> None:
        self.settings = Settings()
        self.local_model = OllamaModel()
        self.model_available = False

        # Initialize cloud models if API keys are available
        self.claude_model = None
        self.gemini_model = None

        if self.settings.claude_api_key:
            self.claude_model = ClaudeModel(self.settings.claude_api_key)

        if self.settings.google_api_key:
            self.gemini_model = GeminiModel(self.settings.google_api_key)

        self._cloud_providers: Dict[str, Dict[str, Any]] = {
            "claude": {
                "name": "Claude (Anthropic)",
                "env_var": "CLAUDE_API_KEY",
                "model": self.claude_model,
            },
            "gemini": {
                "name": "Gemini (Google)",
                "env_var": "GOOGLE_API_KEY",
                "model": self.gemini_model,
            },
        }

        # Default to local model, but allow cloud model selection
        self.current_model: Union[
            OllamaModel, ClaudeModel, GeminiModel
        ] = self.local_model
        self.current_model_name = "local"

    async def initialize(self) -> Dict[str, Any]:
        """Initialize the model manager and ensure model availability."""
        # First check if Ollama is already running
        self.model_available = await self.local_model.is_available()

        if not self.model_available:
            # Try to start Ollama automatically
            startup_result = await self._auto_start_ollama()
            if startup_result:
                # Wait longer for Ollama to fully initialize and load model
                for i in range(10):  # Try for up to 10 seconds
                    await asyncio.sleep(1)
                    self.model_available = await self.local_model.is_available()
                    if self.model_available:
                        break

        if self.model_available:
            health = await self.local_model.health_check()
            return {
                "available": True,
                "message": "🤖 CodeLlama connected! Ready to help with your code.\n",
                "model": health.get("model", "Unknown"),
                "response_time_ms": health.get("response_time_ms", 0),
            }
        else:
            return {
                "available": True,  # Still show as available for fallback
                "message": "⚙️ Ollama service starting... This may take a moment.\n",
                "suggestion": "💡 Try your first command - Ollama will auto-connect. Cloud providers available via /api.\n",
            }

    async def _auto_start_ollama(self) -> bool:
        """Attempt to auto-start Ollama service."""
        try:
            # Check if ollama is installed
            result = subprocess.run(
                ["which", "ollama"], capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                return False  # Ollama not installed

            # Try to start Ollama in the background
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )

            return True

        except Exception:
            return False

    async def get_api_status(self) -> str:
        """Get status of all available API providers."""
        status_lines = ["🌐 **API Provider Status:**\n"]

        # Local model status
        if self.model_available:
            health = await self.local_model.health_check()
            status_lines.append(
                f"✅ **Local**: Ollama ({health.get('model', 'Unknown')}) - {health.get('response_time_ms', 0)}ms"
            )
        else:
            status_lines.append("⚙️ **Local**: Ollama (starting up...)")

        # Check cloud providers
        for provider_id, provider_info in self._cloud_providers.items():
            env_var = str(provider_info["env_var"])
            name = str(provider_info["name"])
            model = provider_info["model"]

            if model is not None:
                status_lines.append(f"🔑 **Cloud**: {name} (API key configured)")
            else:
                status_lines.append(f"❌ **Cloud**: {name} (no API key - set {env_var})")

        status_lines.append("\n💡 **Tips:**")
        status_lines.append("- Local models are private and free")
        status_lines.append("- Cloud models are faster but require API keys")
        status_lines.append("- Set environment variables for cloud access")

        return "\n".join(status_lines) + "\n"

    async def get_status(self) -> str:
        """Get detailed model status."""
        if not self.model_available:
            return "❌ AI Model unavailable. Please start Ollama: ollama serve\n"

        health = await self.local_model.health_check()
        if health["available"]:
            return f"✅ AI Model: {health['model']} (Response time: {health.get('response_time_ms', 0)}ms)\n"
        else:
            return f"❌ AI Model unavailable: {health.get('error', 'Unknown error')}\n"

    async def switch_model(self, model_name: str) -> str:
        """Switch to a different AI model."""
        if model_name in ["local", "ollama"]:
            self.current_model = self.local_model
            self.current_model_name = "local"
            return "🤖 Switched to Local model (Ollama)\n"

        elif model_name == "claude":
            if self.claude_model is not None:
                self.current_model = self.claude_model
                self.current_model_name = "claude"
                return "🧠 Switched to Claude (Anthropic)\n"
            else:
                return "❌ Claude not available. Please set CLAUDE_API_KEY in your .env file\n"

        elif model_name == "gemini":
            if self.gemini_model is not None:
                self.current_model = self.gemini_model
                self.current_model_name = "gemini"
                return "✨ Switched to Gemini (Google)\n"
            else:
                return "❌ Gemini not available. Please set GOOGLE_API_KEY in your .env file\n"

        return f"❌ Unknown model '{model_name}'. Available: local, claude, gemini\n"

    def get_current_model_name(self) -> str:
        """Get the name of the currently active model for styling."""
        return self.current_model_name

    def is_model_available(self) -> bool:
        """Check if the current model is available."""
        return self.model_available
