# File: app_v2/utils/pdf_qdrant_2.py

import io
import logging
import uuid
from typing import Union

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app_v2.config import settings
from app_v2.utils.pdf_prepro import pdf_read_2, get_chunks
from app_v2.utils.model_management import embeddings_model_large

logger = logging.getLogger(__name__)


def handle_pdf_3(file_bytes: Union[bytes, io.BytesIO], file_name: str) -> dict:
    """
    1) Wrap raw bytes in BytesIO if needed.
    2) pdf_read_2 → get_chunks → embed all chunks.
    3) Upsert points into Qdrant with metadata {"page":…, "file_name": file_name}.
    Returns: { "ingested_count": <number_of_chunks> }.
    """

    # 1) Wrap bytes in BytesIO
    if isinstance(file_bytes, (bytes, bytearray)):
        pdf_stream = io.BytesIO(file_bytes)
    elif isinstance(file_bytes, io.BytesIO):
        pdf_stream = file_bytes
    else:
        raise ValueError("handle_pdf_3 expects raw bytes or io.BytesIO")

    # 2) Extract and chunk
    try:
        raw_text_with_metadata = pdf_read_2(pdf_stream)
    except Exception as e:
        logger.error(f"[handle_pdf_3] PDF parsing failed: {e}")
        raise

    try:
        text_chunks_with_metadata = get_chunks(raw_text_with_metadata)
    except Exception as e:
        logger.error(f"[handle_pdf_3] Chunking failed: {e}")
        raise

    if not text_chunks_with_metadata:
        raise ValueError("No chunks extracted from PDF")

    # 3) Batch‐embed all chunk texts
    chunk_texts = [text_string for metadata, text_string in text_chunks_with_metadata]
    try:
        embeddings = embeddings_model_large.embed_documents(chunk_texts)
    except Exception as e:
        logger.error(f"[handle_pdf_3] Embedding failed: {e}")
        raise

    # 4) Ensure Qdrant collection exists
    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    collection_name = settings.PDF_COLLECTION

    try:
        client.get_collection(collection_name=collection_name)
    except Exception:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

    # 5) Build and upsert PointStructs
    points = []
    for idx, (metadata, chunk_text_string) in enumerate(text_chunks_with_metadata):
        base_meta = metadata.copy() if metadata else {}
        base_meta["file_name"] = file_name

        point_id = str(uuid.uuid4())
        points.append(
            PointStruct(
                id=point_id,
                vector=embeddings[idx],
                payload=base_meta
            )
        )

    try:
        client.upsert(collection_name=collection_name, points=points)
    except Exception as e:
        logger.error(f"[handle_pdf_3] Qdrant upsert failed: {e}")
        raise

    ingested_count = len(points)
    logger.info(f"[handle_pdf_3] Ingested {ingested_count} chunks into '{collection_name}'")
    return {"ingested_count": ingested_count}
