import pytest
from openai.error import OpenAIError

from anki_convo.error import LLMError
from anki_convo.llms.openai import OpenAI


@pytest.fixture
def openai_llm():
    return OpenAI(model="test-model")


def test_openai_call(openai_llm, mocker):
    mock_response = mocker.Mock(
        choices=[mocker.Mock(message=mocker.Mock(content="Hello, world!"))]
    )

    mock_create = mocker.patch(
        "openai.ChatCompletion.create", return_value=mock_response
    )

    prompt = "What is the meaning of life?"
    response = openai_llm(prompt)

    mock_create.assert_called_once_with(
        model="test-model",
        messages=[{"role": "user", "content": prompt}],
    )
    assert response == "Hello, world!"


def test_openai_error(openai_llm, mocker):
    """Test that an OpenAIError is raised as an LLMError."""
    mock_create = mocker.patch(
        "openai.ChatCompletion.create",
        side_effect=OpenAIError("Something went wrong"),
    )

    with pytest.raises(LLMError):
        openai_llm("Hello, world!")

    mock_create.assert_called_once_with(
        model="test-model",
        messages=[{"role": "user", "content": "Hello, world!"}],
    )
