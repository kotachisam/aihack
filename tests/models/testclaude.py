from unittest.mock import AsyncMock, Mock

import pytest

from aihack.models.claude import ClaudeModel


@pytest.mark.asyncio
async def test_code_review_basic() -> None:
    # Mock the anthropic client
    mock_client = Mock()
    mock_message = Mock()
    mock_message.content = [
        Mock(text="This code looks good! The function returns 42 as expected.")
    ]
    mock_client.messages.create = AsyncMock(return_value=mock_message)

    agent = ClaudeModel(api_key="test-api-key")
    agent.client = mock_client  # Replace with mock

    code_sample = "def foo(): return 42"
    task = "check correctness"

    response = await agent.code_review(code_sample, task)

    assert isinstance(response, str)
    assert "code looks good" in response.lower()

    # Verify the API was called correctly
    mock_client.messages.create.assert_called_once()
    call_args = mock_client.messages.create.call_args
    assert call_args[1]["model"] == "claude-3-5-sonnet-20241022"
    assert call_args[1]["max_tokens"] == 1000
    assert "check correctness" in call_args[1]["messages"][0]["content"]
