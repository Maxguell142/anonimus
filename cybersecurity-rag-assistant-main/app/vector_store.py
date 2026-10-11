import chromadb
import uuid

from app.config import (
    CHROMA_PATH,
    COLLECTION_NAME
)


client = chromadb.PersistentClient(
    path=CHROMA_PATH
)


collection = client.get_or_create_collection(
    COLLECTION_NAME
)


def store_documents(chunks, embeddings):

    ids=[
        str(uuid.uuid4())
        for _ in chunks
    ]


    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings
    )



def search(query_embedding, k=10):

    result = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=k
    )


    return result["documents"][0]