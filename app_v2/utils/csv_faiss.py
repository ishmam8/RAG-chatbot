import io
import logging
import os
import uuid
import tempfile
from typing import Union

import pandas as pd
from langchain.docstore.document import Document
from langchain_community.document_loaders import CSVLoader
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from app_v2.config import settings

logger = logging.getLogger(__name__)

# Instantiate the embedding model once
_embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=settings.OPENAI_API_KEY
)


def csv_faiss_hybrid_retriever(data, column_contents, project_id, file_name):
    # Ensure FAISS folder exists
    faiss_folder = os.path.join(settings.FAISS_PDF_PATH, project_id)
    os.makedirs(faiss_folder, exist_ok=True)

    docs = list(data)
    for col, text in column_contents.items():
        docs.append(Document(page_content=text, metadata={"column": col, "file_name": file_name, "type": "column"}))

    # Load or create FAISS index
    try:
        faiss_index = FAISS.load_local(folder_path=faiss_folder, embeddings=_embeddings_model)
        logger.info(f"[handle_csv] Loaded existing FAISS index from {faiss_folder}")

        # Duplicate check: skip if file_name already exists
        existing_file_names = set()
        for doc in faiss_index.docstore._dict.values():
            if hasattr(doc, "metadata") and "file_name" in doc.metadata:
                existing_file_names.add(doc.metadata["file_name"])
        if file_name in existing_file_names:
            logger.info(f"[handle_csv] File '{file_name}' already exists in FAISS index. Skipping insertion.")
            return {"ingested_count": 0}

    except Exception:
        faiss_index = FAISS.from_documents(docs, _embeddings_model)
        logger.info(f"[handle_csv] Created new FAISS index with {len(docs)} rows")
        faiss_index.save_local(faiss_folder)
        return {"ingested_count": len(docs)}

    # Add new documents
    faiss_index.add_documents(docs)
    logger.info(f"[handle_csv] Added {len(docs)} new docs (rows+columns) to FAISS index at {faiss_folder}")

    # Save index back to disk
    faiss_index.save_local(faiss_folder)
    return {"ingested_count": len(docs)}


def handle_csv(project_id, uploaded_file, file_name=None):
    raw_data = uploaded_file.getvalue() if hasattr(uploaded_file,"getvalue") else uploaded_file.file.read()
    bio = io.BytesIO(raw_data)

    loader = CSVLoader(file_path=bio, encoding="utf-8", csv_args={'delimiter': ','})
    data = loader.load()
    if not data:
        logger.error("No data found in the CSV.")
        return

    column_contents = {}
    for doc in data:
        for key, value in doc.metadata.items():  # Extract metadata fields
            column_contents.setdefault(key, []).append(str(value))  # Ensure it's a string
        column_contents.setdefault("content", []).append(doc.page_content)  # Store main text content
    column_contents = {col: " ".join(values) for col, values in column_contents.items()}
    
    retriever = csv_faiss_hybrid_retriever(data, column_contents, project_id, uploaded_file.name)
    logger.info("CSV embedding saved into Vector Database successfully with retriever: %s", retriever)
