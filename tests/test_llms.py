import pytest

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
