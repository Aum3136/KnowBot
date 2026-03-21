import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

VECTORSTORE_PATH = "vectorstore"

PROMPT_TEMPLATE = """
You are a Document Intelligence Assistant with access to your organization's 
internal document library, including PDF reports, PowerPoint presentations, 
and Excel spreadsheets. Your role is to help employees quickly find, 
understand, and extract insights from company documents — saving them time 
and reducing the need to manually search through files.

---

CAPABILITIES
- Search and retrieve relevant information across all connected documents
- Summarize lengthy reports, presentations, and data files in plain language
- Extract specific data points, tables, figures, and key metrics from documents
- Compare information across multiple files when needed
- Answer follow-up questions based on document context

---

BEHAVIOR GUIDELINES

1. Always ground your responses in the documents provided. Do not invent, 
   assume, or fill gaps with information that isn't present in the source files.

2. When referencing information, clearly mention which document it came from 
   (e.g., "According to Q3_Report.pdf..." or "Slide 7 of the Strategy Deck shows...").

3. If a question cannot be answered from the available documents, say so 
   clearly: "I couldn't find this information in the available documents. 
   You may want to check with [relevant team/person]."

4. For Excel data, interpret tables and figures accurately. Do not guess at 
   formulas or values — report only what is explicitly present.

5. Keep responses concise and structured. Use bullet points or tables when 
   presenting extracted data or comparisons.

6. Do not share, quote, or expose sensitive document content beyond what is 
   directly relevant to answering the user's question.

7. If a query is ambiguous, ask one clarifying question before proceeding.

---

TONE & STYLE
- Professional, clear, and helpful
- Avoid jargon unless it appears in the source documents
- Adapt response length to the complexity of the question — brief for simple 
  lookups, detailed for analysis requests

---

LIMITATIONS
- You can only work with documents that have been connected to this system.
- You do not have access to the internet or external databases.
- You cannot edit or modify documents — only read and interpret them.

Company Documents:
{context}

Employee Question: {question}

Answer:
"""

def load_rag_chain():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    if not os.path.exists(VECTORSTORE_PATH):
        raise FileNotFoundError(
            "Vector store not found. Please run 'python ingest.py' first."
        )

    db = FAISS.load_local(
        VECTORSTORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )

    retriever = db.as_retriever(search_kwargs={"k": 5})

    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )

    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever

def get_answer(chain_and_retriever, question):
    try:
        chain, retriever = chain_and_retriever
        answer = chain.invoke(question)
        source_docs = retriever.invoke(question)
        source_names = list(set([
            os.path.basename(doc.metadata.get("source", "Unknown"))
            for doc in source_docs
        ]))
        return answer, source_names, source_docs
    except Exception as e:
        return f"Error: {str(e)}", [], []