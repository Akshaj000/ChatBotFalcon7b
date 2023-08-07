import os
import re

from dotenv import find_dotenv, load_dotenv
from langchain import (
    HuggingFaceHub,
    ConversationChain,
    PromptTemplate,
    LLMChain,
)
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseOutputParser
# import langchain
# langchain.debug = True
load_dotenv(find_dotenv())


class CleanupOutputParser(BaseOutputParser):
    def parse(self, text: str) -> str:
        print(text)
        match = re.search(r"(Human:|AI:|User)", text)
        if match:
            index = match.start()
            result = text[:index]
        else:
            result = text

        result = result.strip()
        return result

    @property
    def _type(self) -> str:
        return "output_parser"


TEMPLATE = """
The following is a conversation between a human and an AI. You need to reply to the human's messages.
AI should only reply to the most recent exchange of the Human.
While returning code, wrap it inside ```. Also include the language for example ```python.
If you don't know the answer, just reply with "I don't know".
Current conversations:
{history}
Human: {input}
AI: 
"""

RETRIEVAL_TEMPLATE = """
The following is a conversation between a human and an AI. You need to reply to the human's messages.
AI should only reply to the most recent exchange of the Human.
While returning code, wrap it inside ```. Also include the language for example ```python.
Use the following pieces of context delimited by %%% to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.
%%%{context}%%%
Current conversations:
{history}
Human: {input}
AI:
"""


class LLM:
    def __init__(
        self,
        model_id='tiiuae/falcon-7b-instruct',
        api_key=os.environ['API_KEY']
    ):
        self.vectordb = None
        self.model_id = model_id
        self.llm = HuggingFaceHub(
            huggingfacehub_api_token=api_key,
            repo_id=model_id,
            model_kwargs={"temperature": 0.1, "max_new_tokens": 2000}
        )

        self.template = TEMPLATE.strip()
        self.retrieval_template = RETRIEVAL_TEMPLATE.strip()

        self.prompt = PromptTemplate(
            input_variables=["history", "input"],
            template=self.template
        )

        self.retrieval_prompt = PromptTemplate(
            input_variables=["history", "context", "input"],
            template=self.retrieval_template
        )

        self.memory = ConversationBufferWindowMemory(
            memory_key="history",
            k=2,
            return_only_outputs=True,
            input_key="input"
        )

        self.chain = ConversationChain(
            llm=self.llm,
            verbose=True,
            prompt=self.prompt,
            output_parser=CleanupOutputParser(),
            memory=self.memory,
        )

        self.retrieval_chain = LLMChain(
            llm=self.llm,
            verbose=True,
            prompt=self.retrieval_prompt,
            output_parser=CleanupOutputParser(),
            memory=self.memory,
        )

    def predict(self, message):
        if self.vectordb is not None:
            docs = self.vectordb.similarity_search(message, k=1)
            try:
                output = self.retrieval_chain.predict(
                    input=message,
                    context=docs[0].page_content
                )
            except Exception:
                output = self.chain.predict(input=message)
        else:
            output = self.chain.predict(input=message)
        return output

    def load_document(self):
        from langchain.document_loaders import PyPDFium2Loader
        from langchain.text_splitter import CharacterTextSplitter
        from langchain.vectorstores import Chroma
        from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings

        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len
        )
        loader = PyPDFium2Loader("api/static/uploads/uploaded_document.pdf")
        pages = loader.load()
        docs = text_splitter.split_documents(pages)

        embedding = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vectordb = Chroma.from_documents(
            documents=docs,
            embedding=embedding,
            persist_directory="api/docs/chroma/"
        )


__all__ = ["LLM"]
