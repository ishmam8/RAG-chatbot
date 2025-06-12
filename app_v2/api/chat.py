import os
import sys
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Tuple

# Ensure project root is on PATH so we can import app_v2
sys.path.append(os.getcwd())

from app_v2.schemas import ChatQuery, ChatResponse
from app_v2.config import settings
from app_v2.core.auth import get_current_user
from app_v2.core.model_management import get_embeddings_model, get_llm_chat

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

router = APIRouter(tags=["chat"])

def load_faiss_index_for_project(project_id: str, top_k: int):
    faiss_folder = os.path.join(settings.FAISS_PDF_PATH, project_id)
    if not os.path.isdir(faiss_folder):
        raise HTTPException(
            status_code=404,
            detail=f"No FAISS index found for project'{project_id}'."
        )
    try:
        vectorstore = FAISS.load_local(
            folder_path=faiss_folder,
            embeddings=get_embeddings_model(),
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load FAISS for project '{project_id}': {e}"
        )
    # Return a FAISS retriever that searches all files in the project (no file-level filtering)
    return vectorstore.as_retriever(search_kwargs={"k": top_k})

#TODO:
# Make this route for active users only
@router.post("/query", response_model=ChatResponse)
async def chat_with_pdf(body: ChatQuery, current_user=Depends(get_current_user)):
    # Load a retriever for the requested PDF
    retriever = load_faiss_index_for_project(
        project_id=body.project_id,
        top_k=body.top_k or 4
    )

    # Build a ConversationalRetrievalChain
    chain = ConversationalRetrievalChain.from_llm(
        llm=get_llm_chat(),
        retriever=retriever,
        return_source_documents=True
    )

    # Run the chain with question + history
    result = chain({
        "question": body.question,
        "chat_history": body.history or []
    })

    answer = result["answer"]
    source_docs = result.get("source_documents", [])
    sources = []
    for doc in source_docs:
        meta = doc.metadata  
        page = meta.get("page")
        if page is not None and page not in sources:
            sources.append(f"[Page {page}]")

    # Append this turn to history
    updated_history = (body.history or []) + [(body.question, answer)]

    return ChatResponse(
        answer=answer,
        sources=sources,
        updated_history=updated_history
    )
