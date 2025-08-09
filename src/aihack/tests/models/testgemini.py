from unittest.mock import AsyncMock, Mock

import pytest

from aihack.models.gemini import GeminiModel


@pytest.mark.asyncio
async def test_gemini_code_review() -> None:
    # Mock the Gemini model
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = "This code is well-structured. Consider adding error handling."
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    agent = GeminiModel(api_key="test-api-key")
    agent.model = mock_model  # Replace with mock

    code_sample = "def divide(a, b): return a / b"
    task = "error handling"

    response = await agent.code_review(code_sample, task)

    assert isinstance(response, str)
    assert "error handling" in response.lower()

    # Verify the API was called
    mock_model.generate_content_async.assert_called_once()


@pytest.mark.asyncio
async def test_gemini_optimize_code() -> None:
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = (
        "Optimized version:\ndef divide(a: float, b: float) -> float:\n    return a / b"
    )
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    agent = GeminiModel(api_key="test-api-key")
    agent.model = mock_model

    code_sample = "def divide(a, b): return a / b"
    response = await agent.code_review(code_sample, "optimize")

    assert isinstance(response, str)
    assert "optimized" in response.lower()
    mock_model.generate_content_async.assert_called_once()
