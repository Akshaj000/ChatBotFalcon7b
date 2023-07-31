import re
import os
from dotenv import find_dotenv, load_dotenv
from flask import Flask, render_template, request
from langchain import (
    HuggingFaceHub,
    LLMChain,
    PromptTemplate
)
# from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseOutputParser

load_dotenv(find_dotenv())

model_id = 'tiiuae/falcon-7b-instruct'
falcon_llm = HuggingFaceHub(
    huggingfacehub_api_token=os.environ['API_KEY'],
    repo_id=model_id,
    model_kwargs={"temperature": 0.1, "max_new_tokens": 2000}
)

template = """
You are an AI chatbot. You are helping a human with their daily tasks and queries. You greet people when they greet you. You are good at programming.
{question}  
"""


class CleanupOutputParser(BaseOutputParser):
    def parse(self, text: str) -> str:
        user_pattern = r"\nUser"
        text = re.sub(user_pattern, "", text)
        return text.strip()

    @property
    def _type(self) -> str:
        return "output_parser"


def factory(message):
    prompt = PromptTemplate(
        input_variables=["question"],
        template=template
    )
    llm_chain = LLMChain(
        llm=falcon_llm,
        verbose=True,
        prompt=prompt,
        output_parser=CleanupOutputParser(),
        # memory=ConversationBufferWindowMemory(
        #     memory_key="history",
        # )
    )
    output = llm_chain(message)
    return output['text'] or ""


# web GUI
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        if data is None or "message" not in data:
            return "Invalid JSON data or missing 'message' field.", 400
        message = data["message"]
        processed_message = factory(message)
        if processed_message is None:
            return "Error processing the message.", 500
        return processed_message
    except Exception as e:
        return "An error occurred: {}".format(str(e)), 500


if __name__ == '__main__':
    app.run(debug=True)
