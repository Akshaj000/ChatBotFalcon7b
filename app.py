import os
import re

from dotenv import find_dotenv, load_dotenv
from flask import Flask, render_template, request
from langchain import HuggingFaceHub, LLMChain, PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseOutputParser

load_dotenv(find_dotenv())

model_id = 'tiiuae/falcon-7b-instruct'
falcon_llm = HuggingFaceHub(
    huggingfacehub_api_token=os.environ['API_KEY'],
    repo_id=model_id,
    model_kwargs={"temperature": 0.8, "max_new_tokens": 2000}
)

template = """
The following is a conversation between a human and an AI. The AI is knowledgeable in various fields and is here to 
assist human with any questions they have. AI can also solve coding problems and help with debugging. When returning code snippets,
ai will wrap them inside ```.
Current conversation:
{history}
Human: {input}
AI:""".strip()


class CleanupOutputParser(BaseOutputParser):
    def parse(self, text: str) -> str:
        user_pattern = r"\nUser"
        text = re.sub(user_pattern, "", text)
        human_pattern = r"\nHuman:"
        text = re.sub(human_pattern, "", text)
        ai_pattern = r"\nAI:"
        return re.sub(ai_pattern, "", text).strip()

    @property
    def _type(self) -> str:
        return "output_parser"


def factory(message):
    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template=template
    )
    llm_chain = LLMChain(
        llm=falcon_llm,
        prompt=prompt,
        verbose=True,
        output_parser=CleanupOutputParser(),
        memory=ConversationBufferWindowMemory(
            memory_key="history",
            k=6,
            return_only_outputs=True
        )
    )
    output = llm_chain(message)
    return output['text']


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