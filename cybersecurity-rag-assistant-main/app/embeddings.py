from langchain_huggingface import HuggingFaceEmbeddings
from app.config import EMBEDDING_MODEL


embedding_model = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-en-v1.5"
)


def create_embeddings(texts):

    return embedding_model.embed_documents(texts)


def embed_query(query):

    return embedding_model.embed_query(query)