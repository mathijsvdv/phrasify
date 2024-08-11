import requests

from phrasify.llms.openai import OpenAI

# %%
url = "https://api.openai.com/v1/chat/completions"
messages = [{"role": "user", "content": "How are you?"}]
json = {"model": "gpt-3.5-turbo", "messages": messages}

# %%


# %%
resp = OpenAI()("How are you?")

# %%
response = requests.post(url, json=json, timeout=30)
