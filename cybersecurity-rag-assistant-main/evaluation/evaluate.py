from app.retriever import retrieve
from app.rag_pipeline import answer_question
from evaluation.test_data import test_data
from evaluation.metrics import retrieval_score

import time
import pandas as pd

def run_evaluation():

    results = []

    for item in test_data:

        start = time.time()

        docs = retrieve(
            item["question"]
        )

        answer = answer_question(
            item["question"]
        )

        score = retrieval_score(
            item["question"],
            docs
        )

        results.append(
            {
                "question": item["question"],
                "answer": answer,
                "retrieval_score": score,
                "latency": time.time()-start
            }
        )

    return pd.DataFrame(results)

if __name__ == "__main__":
    result = run_evaluation()

    print("\n===== EVALUATION RESULTS =====")

    print(
        result
    )