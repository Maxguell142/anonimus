# Cybersecurity RAG Assistant

An industry-style Retrieval Augmented Generation (RAG) system combining
cybersecurity knowledge retrieval with Large Language Models.

Built with LangChain, ChromaDB, HuggingFace Embeddings, Cross-Encoder
Reranking, Ollama LLM, FastAPI, Docker, and evaluation pipelines.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![LangChain](https://img.shields.io/badge/LangChain-RAG-green)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![ChromaDB](https://img.shields.io/badge/VectorDB-Chroma-orange)
------------------------------------------------------------------------

## Project Overview

This project builds an AI-powered cybersecurity assistant that:

-   Ingests cybersecurity documents
-   Converts documents into semantic embeddings
-   Stores knowledge in ChromaDB
-   Retrieves relevant context
-   Applies reranking for better relevance
-   Generates grounded answers using an LLM
-   Evaluates retrieval quality and latency

------------------------------------------------------------------------

## Architecture

Cybersecurity Documents → Document Processing → Recursive Chunking → HuggingFace Embeddings → 
ChromaDB Vector Database → Similarity Retrieval → Cross Encoder Reranker → Relevant Context → 
Ollama LLM → Final Answer

------------------------------------------------------------------------

## Key Features

### Semantic Search

Uses embeddings to understand meaning instead of only matching keywords.

Example:

Question: “What is ransomware?”

Can retrieve content about:

-   file encryption
-   malware
-   extortion
-   payment demands

------------------------------------------------------------------------

## Retrieval Augmented Generation

The system separates:

Retrieval: Finding relevant cybersecurity knowledge

Generation: Creating the final response

This reduces hallucinations and improves accuracy.

------------------------------------------------------------------------

## Reranking Pipeline

Initial retrieval:

Query | Embedding | ChromaDB | Top 10 documents

Then:

Top 10 | Cross Encoder Reranker | Top 3 documents | LLM

Benefits:

-   Higher precision
-   Less irrelevant context
-   Better answers

------------------------------------------------------------------------

## Technology Stack

AI / ML: - LangChain - HuggingFace Transformers - Sentence
Transformers - Ollama - RAGAS

Vector Database: - ChromaDB

Backend: - FastAPI - Uvicorn

DevOps: - Docker - Docker Compose

------------------------------------------------------------------------

## Project Structure

app/ - main.py - rag_pipeline.py - retriever.py - reranker.py -
embeddings.py - vector_store.py - llm.py - config.py

evaluation/ - test_data.py - metrics.py - evaluate.py

data/ - raw_docs/

------------------------------------------------------------------------

## Evaluation

The project evaluates:

Retrieval Score

Measures if retrieved documents contain expected concepts.

Latency

Tracks total response time:

Query -> Retrieval -> Reranking -> Generation

------------------------------------------------------------------------

## Example Evaluation Dataset

MITRE ATT&CK: Tests attacker behavior and threat modeling knowledge.

CIS Controls v8: Tests defensive security controls.

OWASP Top 10 for LLMs: Tests AI security knowledge.

------------------------------------------------------------------------

## API

Run:

uvicorn app.main:app –reload

Swagger:

http://localhost:8000/docs

Example:

POST /ask

{ “question”: “What is MITRE ATT&CK?” }

------------------------------------------------------------------------

## Docker Deployment

Build:

docker compose build

Run:

docker compose up

------------------------------------------------------------------------

## Engineering Practices

Demonstrates:

-   Modular Python architecture
-   REST API development
-   Vector database implementation
-   ML evaluation workflow
-   Containerization
-   Local LLM deployment
-   Production-style project organization

------------------------------------------------------------------------

## Future Improvements

-   Hybrid search (BM25 + vector)
-   Query rewriting
-   Authentication
-   Monitoring
-   Cloud deployment
-   Advanced evaluation metrics

------------------------------------------------------------------------

### Author: Chirag Handa | AI / ML Engineer | Cybersecurity Analyst | Backend Development
