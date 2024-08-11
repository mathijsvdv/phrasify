from dataclasses import asdict

import requests

from phrasify.card import TranslationCard
from phrasify.card_gen import CardGeneratorConfig, create_card_generator

api_url = "http://localhost:8800/v1/cards"


card_generator_config = CardGeneratorConfig(
    llm="gpt-3.5-turbo",
    prompt_name="vocab-to-sentence",
    source_language="English",
    target_language="Ukrainian",
    n_cards=1,
)
card = TranslationCard(source="friend", target="друг")

request_json = {"card_generator": asdict(card_generator_config), "card": asdict(card)}
response = requests.post(api_url, json=request_json, timeout=30)
response_json = response.json()
print(f"Cards from direct API call: {response_json}")


remote_card_generator = create_card_generator(card_generator_config, api_url)
print(f"Remote card generator: {remote_card_generator}")
cards = remote_card_generator(card)

print(f"Cards from remote card generator: {cards}")
