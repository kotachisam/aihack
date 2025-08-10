from unittest.mock import AsyncMock, Mock

import pytest

from aihack.models.local import OllamaModel


@pytest.mark.asyncio
async def test_ollama_code_review() -> None:
    # Mock the httpx client
    mock_client = Mock()
    mock_response = Mock()
    mock_response.json.return_value = {
        "response": "This function looks correct. It returns 42 as expected."
    }
    mock_client.post = AsyncMock(return_value=mock_response)

    agent = OllamaModel()
    agent.client = mock_client  # Replace with mock

    code_sample = "def foo(): return 42"
    task = "correctness"

    response = await agent.code_review(code_sample, task)

    assert isinstance(response, str)
    assert "42" in response

    # Verify the API was called correctly
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "/api/generate" in str(call_args)


@pytest.mark.asyncio
async def test_ollama_availability_check() -> None:
    # Mock successful availability check
    mock_client = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_client.get = AsyncMock(return_value=mock_response)

    agent = OllamaModel()
    agent.client = mock_client

    is_available = await agent.is_available()

    assert is_available is True
    mock_client.get.assert_called_once_with("/api/tags", timeout=5.0)


@pytest.mark.asyncio
async def test_ollama_unavailable() -> None:
    # Mock failed availability check
    mock_client = Mock()
    mock_client.get = AsyncMock(side_effect=Exception("Connection failed"))

    agent = OllamaModel()
    agent.client = mock_client

    is_available = await agent.is_available()

    assert is_available is False


@pytest.mark.asyncio
async def test_ollama_generate_error_handling() -> None:
    # Mock network error
    mock_client = Mock()
    mock_client.post = AsyncMock(side_effect=Exception("Network error"))

    agent = OllamaModel()
    agent.client = mock_client

    # Expect ModelError to be raised
    with pytest.raises(Exception) as excinfo:
        await agent.generate("test prompt")

    assert "Network error" in str(excinfo.value)
