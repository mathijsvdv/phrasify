from langchain.chains.llm import LLMChain
from langchain.chat_models.openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from phrasify.chains.remote import RemoteChain

api_url = "http://phrasify.mvdvlies.com/chain"
# message = {
#     "input": {
#         "llm": "gpt-3.5-turbo",
#         "prompt": "Make a sentence with for {field_text} in Ukrainian?",
#         "prompt_inputs": {
#             "field_text": "friend"
#         },
#     }
# }

# response = requests.post(api_url + "/invoke", json=message, timeout=30)

# chain = RemoteRunnable(api_url)
# chain_input = {
#     "llm": "gpt-3.5-turbo",
#     "prompt": "Make a sentence with for {field_text} in Ukrainian?",
#     "prompt_inputs": {
#         "field_text": "friend"
#     },
# }
# chain_output = chain.invoke(chain_input)
# print(chain_output)


llm_chain = LLMChain(
    llm=ChatOpenAI(model="gpt-3.5-turbo"),
    prompt=PromptTemplate.from_template(
        "Make a sentence with for {field_text} in Ukrainian"
    ),
)
llm_chain_output = llm_chain("friend")
print(llm_chain_output)

remote_chain = RemoteChain(api_url=api_url)
remote_chain_input = {
    "llm": "gpt-3.5-turbo",
    "prompt": "Make a sentence with for {field_text} in Ukrainian?",
    "prompt_inputs": {"field_text": "friend"},
}
remote_chain_output = remote_chain(remote_chain_input)
print(remote_chain_output)
