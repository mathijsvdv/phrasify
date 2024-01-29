import pytest

from anki_convo.error import LLMError
from anki_convo.llms.openai import OpenAI
from anki_convo.openai import OPENAI_CHAT_COMPLETIONS_URL

from .mocks import MockResponse


@pytest.fixture
def openai_llm():
    return OpenAI(model="test-model", api_key="sk-xxx")


def _assert_requests_post_called(requests_post, prompt):
    messages = [{"role": "user", "content": prompt}]
    request_json = {"model": "test-model", "messages": messages}
    headers = {"Content-Type": "application/json", "Authorization": "Bearer sk-xxx"}
    requests_post.assert_called_once_with(
        OPENAI_CHAT_COMPLETIONS_URL,
        json=request_json,
        headers=headers,
        timeout=30,
    )


def test_openai_call(openai_llm, mocker):
    response_json = {"choices": [{"message": {"content": "Hello, world!"}}]}
    mock_response = MockResponse(json=response_json, status_code=200)

    mock_post = mocker.patch("requests.post", return_value=mock_response)

    prompt = "What is the meaning of life?"
    response = openai_llm(prompt)

    assert response == "Hello, world!"
    _assert_requests_post_called(mock_post, prompt)


def test_openai_error(openai_llm, mocker):
    """Test that a HTTPError is raised as an LLMError."""
    mock_response = MockResponse(json={}, status_code=500)

    mock_post = mocker.patch("requests.post", return_value=mock_response)

    prompt = "What is the meaning of life?"
    with pytest.raises(LLMError):
        openai_llm(prompt)

    _assert_requests_post_called(mock_post, prompt)
