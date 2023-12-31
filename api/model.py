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
import pinecone

load_dotenv(find_dotenv())


pinecone.init(
    api_key=os.environ["PINECONE_API_KEY"],  # api key in console
    environment=os.environ["PINECONE_ENVIRONMENT"],  # environment name
)


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
Use the following pieces of context delimited by %%% to answer the question at the end.
If you don't know the answer, just reply with "I don't know".
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
        self.embedding = None
        self.docs = None
        self.upload_status = "NOT_UPLOADED"
        self.vectordb = None
        self.model_id = model_id
        self.index_name = "falcon-bot"
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

        self.prompt2 = PromptTemplate(
            input_variables=["input"],
            template="{input}"
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

        self.direct_chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt2,
            verbose=True
        )

        self.retrieval_chain = LLMChain(
            llm=self.llm,
            verbose=True,
            prompt=self.retrieval_prompt,
            output_parser=CleanupOutputParser(),
            memory=self.memory,
        )

    def predict(self, message):
        if self.upload_status == "UPLOADED":
            docs = self.vectordb.similarity_search(message, k=1)
            output = self.retrieval_chain.predict(
                input=message,
                context=docs[0].page_content
            )
        else:
            output = self.chain.predict(input=message)
        return output

    def generate(self, message):
        message = self.direct_chain.predict(input=message)
        print(message)
        return message

    def delete_index(self):
        try:
            pinecone.delete_index(self.index_name)
        except Exception:
            pass

    def upload_file(self, file):
        self.upload_status = "UPLOADING"
        import tempfile
        from langchain.document_loaders import PyPDFLoader
        from langchain.text_splitter import CharacterTextSplitter

        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file.read())
                file_path = temp_file.name

            text_splitter = CharacterTextSplitter(
                separator="\n",
                chunk_size=1000,
                chunk_overlap=150,
                length_function=len
            )
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            docs = text_splitter.split_documents(pages)
            self.docs = docs

        except Exception as e:
            self.upload_status = "NOT_UPLOADED"
            print(f"An error occurred during file upload: {str(e)}")

    def create_index(self):
        self.delete_index()
        from langchain.vectorstores import Pinecone
        from langchain.embeddings import HuggingFaceHubEmbeddings
        embedding = HuggingFaceHubEmbeddings(
            repo_id="sentence-transformers/all-MiniLM-L6-v2",
            task="feature-extraction",
            huggingfacehub_api_token=os.environ["API_KEY"],
        )
        self.embedding = embedding
        pinecone.create_index(
            name=self.index_name,
            metric='cosine',
            dimension=384
        )
        self.vectordb = Pinecone.from_documents(
            self.docs,
            embedding=self.embedding,
            index_name=self.index_name,
        )
        self.upload_status = "UPLOADED"


__all__ = ["LLM"]
