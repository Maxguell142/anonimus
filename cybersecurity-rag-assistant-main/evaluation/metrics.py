from app.embeddings import embed_query
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np



def retrieval_score(query, docs):

    query_vector = embed_query(query)

    doc_vectors = [
        embed_query(doc)
        for doc in docs
    ]


    scores = cosine_similarity(
        [query_vector],
        doc_vectors
    )[0]


    return float(
        np.max(scores)
    )