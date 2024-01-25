import pytest

from anki_convo.card import TranslationCard
from anki_convo.card_gen import LLMTranslationCardGenerator
from anki_convo.chains.llm import LLMChain
from anki_convo.factory import get_prompt
from anki_convo.llms.openai import OpenAI


@pytest.fixture(params=[0, 1, 3, 5])
def n_cards(request):
    return request.param


# TODO: Add a test for the case where the chain raises an error
@pytest.fixture()
def llm_translation_card_generator(n_cards):
    chain = LLMChain(
        llm=OpenAI(model="gpt-3.5-turbo"), prompt=get_prompt("vocab-to-sentence")
    )

    generator = LLMTranslationCardGenerator(
        chain=chain,
        n_cards=n_cards,
        source_language="English",
        target_language="Ukrainian",
    )
    return generator


@pytest.fixture(
    params=[("friend", "друг"), ("to give", "давати"), ("love", "любов")],
    ids=["friend", "to give", "love"],
)
def translation_card(request):
    source, target = request.param
    return TranslationCard(source=source, target=target)
