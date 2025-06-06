import io
import logging
import os
import uuid
from typing import Union

from langchain.docstore.document import Document
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from app_v2.config import settings
from app_v2.utils.pdf_prepro import pdf_read_2, get_chunks

logger = logging.getLogger(__name__)

# Instantiate the embedding model once
_embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=settings.OPENAI_API_KEY
)


def handle_pdf_3(file_bytes: Union[bytes, io.BytesIO], file_name: str) -> dict:
    """
    1. Wrap raw bytes in BytesIO if needed.
    2. Extract text → chunk into overlapping Document objects with metadata (incl. page & file_name).
    3. Load or create a FAISS index at settings.FAISS_PDF_PATH.
    4. Add the new chunks/documents to that index and save it.
    Returns: { "ingested_count": <number_of_chunks> }.
    """
    # 1) Wrap raw bytes in BytesIO
    if isinstance(file_bytes, (bytes, bytearray)):
        pdf_stream = io.BytesIO(file_bytes)
    elif isinstance(file_bytes, io.BytesIO):
        pdf_stream = file_bytes
    else:
        raise ValueError("handle_pdf_3 expects raw bytes or io.BytesIO")

    # 2) Extract and chunk
    try:
        raw_text_with_metadata = pdf_read_2(file_name, pdf_stream)
    except Exception as e:
        logger.error(f"[handle_pdf_3] PDF parsing failed: {e}")
        raise

    try:
        text_chunks = get_chunks(raw_text_with_metadata)
    except Exception as e:
        logger.error(f"[handle_pdf_3] Chunking failed: {e}")
        raise

    if not text_chunks:
        raise ValueError("No chunks extracted from PDF")

    # 3) Build LangChain Document objects with metadata
    docs = []
    for metadata, page_text in text_chunks:
        # chunk.metadata already contains page info (e.g. {"page": 3})
        meta = metadata.copy() if metadata else {}
        meta["file_name"] = file_name
        docs.append(Document(page_content=page_text, metadata=meta))

    # 4) Ensure FAISS folder exists
    pdf_key = os.path.splitext(file_name)[0]
    faiss_folder = os.path.join(settings.FAISS_PDF_PATH, pdf_key)
    os.makedirs(faiss_folder, exist_ok=True)

    # 5) Load existing FAISS or create a new one
    try:
        faiss_index = FAISS.load_local(folder_path=faiss_folder, embeddings=_embeddings_model,
                                       allow_dangerous_deserialization=True)
        logger.info(f"Loaded existing FAISS at {faiss_folder}")
        faiss_index.add_documents(docs)
        logger.info(f"Appended {len(docs)} chunks to FAISS at {faiss_folder}")
    except Exception:
        # No existing index on disk → create a new one
        faiss_index = FAISS.from_documents(docs, _embeddings_model)
        logger.info(f"Created new FAISS index with {len(docs)} chunks")
        faiss_index.save_local(faiss_folder)
        return {"ingested_count": len(docs)}

    # 6) Save index back to disk
    faiss_index.save_local(faiss_folder)

    return {"ingested_count": len(docs)}
