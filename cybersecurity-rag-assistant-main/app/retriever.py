from app.embeddings import embed_query
from app.vector_store import search
from app.reranker import rerank



def retrieve(query):

    query_vector = embed_query(query)


    docs = search(
        query_vector,
        k=10
    )


    final_docs = rerank(
        query,
        docs
    )


    return final_docs