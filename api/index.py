import re
import os
from dotenv import find_dotenv, load_dotenv
from flask import Flask, render_template, request
from langchain import (
    HuggingFaceHub,
    ConversationChain,
    PromptTemplate
)
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseOutputParser

load_dotenv(find_dotenv())

model_id = 'tiiuae/falcon-7b-instruct'
falcon_llm = HuggingFaceHub(
    huggingfacehub_api_token=os.environ['API_KEY'],
    repo_id=model_id,
    model_kwargs={"temperature": 0.1, "max_new_tokens": 2000}
)

template = """
The following is a conversation between a user and an AI. You need to reply to the human's message.
While returning a code, please make sure that the code is delimited by the following pattern:```<lang> <code>```
Current conversations:
{history}
Human: {input}
AI:
""".strip()


class CleanupOutputParser(BaseOutputParser):
    def parse(self, text: str) -> str:
        user_pattern = r"\nUser"
        text = re.sub(user_pattern, "", text)
        ai_pattern = r"\nAI:"
        text = re.sub(ai_pattern, "", text)
        human_pattern = r"\nHuman:"
        text = re.sub(human_pattern, "", text)
        return text

    @property
    def _type(self) -> str:
        return "output_parser"


prompt = PromptTemplate(
    input_variables=["history", "input"],
    template=template
)

memory = ConversationBufferWindowMemory(
    memory_key="history", k=4, return_only_outputs=True
)

chain = ConversationChain(
    llm=falcon_llm,
    verbose=True,
    prompt=prompt,
    output_parser=CleanupOutputParser(),
    memory=memory
)


def factory(message):
    output = chain.predict(input=message)
    return output


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
