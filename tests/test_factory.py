import pytest

from phrasify.factory import get_llm


@pytest.mark.parametrize("llm_name", ["gpt-3.5-turbo", "gpt-4"])
def test_get_llm_with_valid_name(llm_name):
    llm = get_llm(llm_name)
    assert llm.model == llm_name


def test_get_llm_with_invalid_name():
    with pytest.raises(ValueError):
        get_llm("invalid-llm")
