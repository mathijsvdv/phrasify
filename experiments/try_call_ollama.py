from phrasify.llms.ollama import Ollama

llm = Ollama(model="mistral")
prompt = """
I want you to act as a professional Anki card creator, able to create Anki cards from the text I provide.

Regarding the formulation of the card content, you stick to two principles:
- First, minimum information principle: The material you learn must be formulated in as simple way as it is only possible. Simplicity does not have to imply losing information and skipping the difficult part.
- Second, optimize wording: The wording of your items must be optimized to make sure that in minimum time the right bulb in your brain lights up. This will reduce error rates, increase specificity, reduce response time, and help your concentration.

You are going to use your skills to generate Anki cards that help memorize vocabulary in a foreign language by generating sentences from the vocabulary words and phrases I provide.

I know the following source language: English, and I want to learn the following target language: Ukrainian.

Please generate 5 card(s) from the following input card in JSON format containing just a vocabulary word or phrase:
{'source': 'friend', 'target': 'друг'}

For each card, I want you to replace the 'source' field with the English sentence and the 'target' field with the Ukrainian sentence.
You should not give any response other than the JSON (list of cards). Not a single character of text aside from JSON.
"""
# prompt = "How are you?"

print(f"Answer: {llm(prompt)}")
