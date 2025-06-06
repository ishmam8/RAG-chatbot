import os
import sys
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Tuple

# Ensure project root is on PATH so we can import app_v2
sys.path.append(os.getcwd())

from app_v2.schemas import ChatQuery, ChatResponse
from app_v2.config import settings
from app_v2.core.auth import get_current_user

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

router = APIRouter(prefix="/chat", tags=["chat"])

def load_faiss_index_for_pdf(file_name: str, top_k: int):
    """
    Given a PDF filename (e.g. "test_pdf.pdf") and desired top_k,
    load the FAISS index from faiss_db/pdf_index/<pdf_name_without_ext> and
    return a retriever configured with that index.
    """
    pdf_key = os.path.splitext(file_name)[0]  # "test_pdf"
    faiss_folder = os.path.join(settings.FAISS_PDF_PATH, pdf_key)

    if not os.path.isdir(faiss_folder):
        raise HTTPException(
            status_code=404,
            detail=f"No FAISS index found for '{file_name}'. Did you upload it?"
        )

    # Re‐instantiate the same embeddings used during ingestion
    embeddings_model = OpenAIEmbeddings(
        model="text-embedding-3-large",
        openai_api_key=settings.OPENAI_API_KEY
    )

    try:
        vectorstore = FAISS.load_local(
            folder_path=faiss_folder,
            embeddings=embeddings_model,
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load FAISS for '{file_name}': {e}"
        )

    # Return a simple FAISS retriever (no metadata filtering needed, since one‐index per PDF)
    return vectorstore.as_retriever(search_kwargs={"k": top_k})


@router.post("/query", response_model=ChatResponse)
async def chat_with_pdf(body: ChatQuery, current_user=Depends(get_current_user)):
    """
    POST /chat/query
    {
      "question": "What does page 2 say?",
      "history": [ ["Hi", "Hello!"] ],
      "file_name": "test_pdf.pdf",
      "top_k": 4
    }

    Returns:
    {
      "answer": "<LLM’s response>",
      "sources": ["[Page 2]", "[Page 1]"],
      "updated_history": [ [...], [question, answer] ]
    }
    """
    # 1) Load a retriever for the requested PDF
    retriever = load_faiss_index_for_pdf(
        file_name=body.file_name,
        top_k=body.top_k or 4
    )

    # 2) Instantiate the same ChatOpenAI model used elsewhere
    llm = ChatOpenAI(
        model_name="gpt-4.5-preview",
        temperature=0,
        openai_api_key=settings.OPENAI_API_KEY
    )

    # 3) Build a ConversationalRetrievalChain
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    # 4) Run the chain with question + history
    result = chain({
        "question": body.question,
        "chat_history": body.history or []
    })

    answer = result["answer"]
    source_docs = result.get("source_documents", [])

    # 5) Collect “sources” as simple “[Page x]” tags
    sources = []
    for doc in source_docs:
        meta = doc.metadata  # e.g. {"page": 2, "file_name": "test_pdf.pdf"}
        page = meta.get("page")
        if page is not None and page not in sources:
            sources.append(f"[Page {page}]")

    # 6) Append this turn to history
    updated_history = (body.history or []) + [(body.question, answer)]

    return ChatResponse(
        answer=answer,
        sources=sources,
        updated_history=updated_history
    )
