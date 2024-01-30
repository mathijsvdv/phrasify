import pytest
import requests

from phrasify.error import LLMError
from phrasify.llms.ollama import Ollama
from phrasify.llms.openai import OpenAI
from phrasify.openai import OPENAI_CHAT_COMPLETIONS_URL

from .mocks import MockResponse


@pytest.fixture
def openai_llm():
    return OpenAI(model="test-model", api_key="sk-xxx")


@pytest.fixture
def ollama_llm():
    return Ollama(model="test-model", url="http://localhost:11434")


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


def _assert_requests_post_called_ollama(requests_post, prompt):
    request_json = {
        "prompt": prompt,
        "model": "test-model",
        "stream": False,
    }
    requests_post.assert_called_once_with(
        "http://localhost:11434/api/generate",
        json=request_json,
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


def test_openai_timeout(openai_llm, mocker):
    """Test that a TimeoutError is raised as an LLMError."""
    mock_post = mocker.patch("requests.post", side_effect=requests.ReadTimeout)

    prompt = "What is the meaning of life?"
    with pytest.raises(LLMError):
        openai_llm(prompt)

    _assert_requests_post_called(mock_post, prompt)


def test_ollama_call(ollama_llm, mocker):
    response_json = {"response": "Hello, world!"}
    mock_response = MockResponse(json=response_json, status_code=200)

    mock_post = mocker.patch("requests.post", return_value=mock_response)

    prompt = "What is the meaning of life?"
    response = ollama_llm(prompt)

    assert response == "Hello, world!"
    _assert_requests_post_called_ollama(mock_post, prompt)


def test_ollama_error(ollama_llm, mocker):
    mock_response = MockResponse(json={}, status_code=500)

    mock_post = mocker.patch("requests.post", return_value=mock_response)

    prompt = "What is the meaning of life?"
    with pytest.raises(LLMError):
        ollama_llm(prompt)

    _assert_requests_post_called_ollama(mock_post, prompt)


def test_ollama_timeout(ollama_llm, mocker):
    """Test that a TimeoutError is raised as an LLMError."""
    mock_post = mocker.patch("requests.post", side_effect=requests.ReadTimeout)

    prompt = "What is the meaning of life?"
    with pytest.raises(LLMError):
        ollama_llm(prompt)

    _assert_requests_post_called_ollama(mock_post, prompt)
