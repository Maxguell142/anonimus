from pypdf import PdfReader
import os


def load_pdf(path):

    reader = PdfReader(path)

    text = ""

    for page in reader.pages:
        content = page.extract_text()

        if content:
            text += content + "\n"

    return text



def load_documents(folder):

    documents=[]

    for file in os.listdir(folder):

        if file.endswith(".pdf"):

            path = os.path.join(folder,file)

            documents.append(
                load_pdf(path)
            )

    return documents