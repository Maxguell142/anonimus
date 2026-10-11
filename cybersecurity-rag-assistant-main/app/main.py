from fastapi import FastAPI
from pydantic import BaseModel

from app.rag_pipeline import answer_question
from evaluation.evaluate import run_evaluation


app = FastAPI(
    title="Cybersecurity RAG Assistant"
)


class QueryRequest(BaseModel):
    question: str



@app.get("/")
def home():

    return {
        "status": "running"
    }



@app.post("/ask")
def ask(request: QueryRequest):

    answer = answer_question(
        request.question
    )

    return {
        "question": request.question,
        "answer": answer
    }



@app.get("/evaluate")
def evaluate():

    results = run_evaluation()

    return results