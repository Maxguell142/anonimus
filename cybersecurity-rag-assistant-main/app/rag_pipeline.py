from app.retriever import retrieve
from app.llm import generate



def answer_question(question):


    context_docs = retrieve(question)


    context="\n".join(context_docs)


    prompt=f"""

You are a cybersecurity assistant.

Use only this context:

{context}


Question:

{question}


Answer:

"""


    return generate(prompt)