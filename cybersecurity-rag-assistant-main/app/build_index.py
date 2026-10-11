from app.ingestion import load_documents
from app.chunking import create_chunks
from app.embeddings import create_embeddings
from app.vector_store import store_documents
from app.config import DATA_PATH


def build_index():

    print("Loading documents...")

    documents = load_documents(
        DATA_PATH
    )

    print(
        f"Loaded {len(documents)} documents"
    )


    print("Creating chunks...")

    chunks = create_chunks(
        documents
    )

    print(
        f"Created {len(chunks)} chunks"
    )


    print("Creating embeddings...")

    embeddings = create_embeddings(
        chunks
    )


    print("Storing in ChromaDB...")

    store_documents(
        chunks,
        embeddings
    )


    print("Index created successfully")


if __name__ == "__main__":

    build_index()