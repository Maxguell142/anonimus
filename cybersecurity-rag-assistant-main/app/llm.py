from langchain_ollama import OllamaLLM
from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    model="llama3.1",
    base_url="http://ollama:11434"
)

def generate(prompt):
    return llm.invoke(prompt)