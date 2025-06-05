import io
import logging
import os
import uuid
from typing import Union

import pandas as pd
from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

from app_v2.config import settings

logger = logging.getLogger(__name__)

# Instantiate the embedding model once
_embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=settings.OPENAI_API_KEY
)


def handle_csv_v2(
    file_bytes: Union[bytes, io.BytesIO],
    file_name: str
) -> dict:
    """
    1. Wrap raw bytes in BytesIO if needed.
    2. Read CSV into DataFrame → build one Document per row, with metadata {"row_index": i, "file_name": file_name}.
    3. Load or create a FAISS index at settings.FAISS_CSV_PATH.
    4. Add these new row-documents → save index.
    Returns: { "ingested_count": <number_of_rows> }.
    """
    # 1) Wrap bytes
    if isinstance(file_bytes, (bytes, bytearray)):
        csv_stream = io.BytesIO(file_bytes)
    elif isinstance(file_bytes, io.BytesIO):
        csv_stream = file_bytes
    else:
        raise ValueError("handle_csv_v2 expects raw bytes or io.BytesIO")

    # 2) Load into DataFrame
    try:
        df = pd.read_csv(csv_stream)
    except Exception as e:
        logger.error(f"[handle_csv_v2] Failed to read CSV: {e}")
        raise

    if df.empty:
        raise ValueError("CSV is empty or unreadable")

    # 3) Build one Document per row
    docs = []
    for idx, row in df.iterrows():
        # Concatenate all non-null values for embedding
        row_text = " ".join(str(val) for val in row.values if pd.notna(val))
        metadata = {"row_index": int(idx), "file_name": file_name}
        docs.append(Document(page_content=row_text, metadata=metadata))

    # 4) Ensure FAISS folder exists
    faiss_folder = settings.FAISS_CSV_PATH
    os.makedirs(faiss_folder, exist_ok=True)

    # 5) Load or create FAISS index
    try:
        faiss_index = FAISS.load_local(folder_path=faiss_folder, embeddings=_embeddings_model)
        logger.info(f"[handle_csv_v2] Loaded existing FAISS index from {faiss_folder}")
    except Exception:
        faiss_index = FAISS.from_documents(docs, _embeddings_model)
        logger.info(f"[handle_csv_v2] Created new FAISS index with {len(docs)} rows")
        faiss_index.save_local(faiss_folder)
        return {"ingested_count": len(docs)}

    # 6) Add new documents
    faiss_index.add_documents(docs)
    logger.info(f"[handle_csv_v2] Added {len(docs)} new rows to FAISS index at {faiss_folder}")

    # 7) Save index back to disk
    faiss_index.save_local(faiss_folder)

    return {"ingested_count": len(docs)}
