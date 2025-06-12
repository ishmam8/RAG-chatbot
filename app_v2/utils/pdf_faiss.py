import io
import logging
import os
import uuid
from typing import Union

from langchain.docstore.document import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from app_v2.config import settings
from app_v2.services import get_project_info
from app_v2.utils.pdf_prepro import pdf_read_2, get_chunks
from app_v2.core.model_management import get_embeddings_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
1. Wrap raw bytes in BytesIO if needed.
2. Extract text → chunk into overlapping Document objects with metadata (incl. page & file_name).
3. Load or create a FAISS index at settings.FAISS_PDF_PATH.
4. Add the new chunks/documents to that index and save it.
Returns: { "ingested_count": <number_of_chunks> }.
"""

def pdf_faiss_hybrid_retriever(text_chunks, project_id, file_name):
    project_name, project_intro = get_project_info(project_id)
    
    # Build LangChain Document objects with metadata
    docs = []
    for metadata, page_text in text_chunks:
        # chunk.metadata already contains page info (e.g. {"page": 3})
        meta = metadata.copy() if metadata else {}
        meta["file_name"] = file_name
        meta["project_name"] = project_name
        meta["project_intro"] = project_intro
        docs.append(Document(page_content=page_text, metadata=meta))

    #Ensure FAISS folder exists
    faiss_folder = os.path.join(settings.FAISS_PDF_PATH, project_id)
    os.makedirs(faiss_folder, exist_ok=True)

    #Load existing FAISS or create a new one
    try:
        faiss_index = FAISS.load_local(folder_path=faiss_folder, embeddings=get_embeddings_model(),
                                       allow_dangerous_deserialization=True)
        logger.info(f"Loaded existing FAISS at {faiss_folder}")
        
        # Check for duplicate file_name
        existing_file_names = set()
        for doc in faiss_index.docstore._dict.values():
            if hasattr(doc, "metadata") and "file_name" in doc.metadata:
                existing_file_names.add(doc.metadata["file_name"])
        if file_name in existing_file_names:
            logger.info(f"File '{file_name}' already exists in FAISS index. Skipping insertion.")
            return {"ingested_count": 0}
        
    except Exception as e:
        logger.warning(f"[handle_csv] Failed to load existing FAISS: {e}")
        
        faiss_index = FAISS.from_documents(docs, get_embeddings_model())
        logger.info(f"Created new FAISS index with {len(docs)} chunks")
        faiss_index.save_local(faiss_folder)
        return {"ingested_count": len(docs)}

    faiss_index.add_documents(docs)
    logger.info(f"Appended {len(docs)} chunks to FAISS at {faiss_folder}")
    faiss_index.save_local(faiss_folder)
    
    return {"ingested_count": len(docs)}


def handle_pdf(project_id, file_bytes: Union[bytes, io.BytesIO], file_name: str) -> dict:
    if isinstance(file_bytes, (bytes, bytearray)):
        pdf_stream = io.BytesIO(file_bytes)
    elif isinstance(file_bytes, io.BytesIO):
        pdf_stream = file_bytes
    else:
        raise ValueError("handle_pdf_3 expects raw bytes or io.BytesIO")

    # Extract and chunk
    try:
        raw_text_with_metadata = pdf_read_2(pdf_stream, file_name)
    except Exception as e:
        logger.error(f"[handle_pdf] PDF parsing failed: {e}")
        raise

    try:
        text_chunks = get_chunks(raw_text_with_metadata)
    except Exception as e:
        logger.error(f"[handle_pdf] Chunking failed: {e}")
        raise

    if not text_chunks:
        raise ValueError("No chunks extracted from PDF")

    retriever = pdf_faiss_hybrid_retriever(text_chunks=text_chunks, project_id=project_id, file_name=file_name)
    
    return retriever
