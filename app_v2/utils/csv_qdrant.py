# File: app_v2/utils/csv_qdrant2.py

import io
import logging
import uuid
from typing import Union

import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app_v2.config import settings
from app_v2.utils.model_management import embeddings_model_large

logger = logging.getLogger(__name__)


def handle_csv_v2(file_bytes: Union[bytes, io.BytesIO], file_name: str) -> dict:
    """
    1) Wrap raw bytes in BytesIO if needed.
    2) Read CSV into DataFrame → for each row: build text + metadata {"row_index": idx, "file_name": file_name}.
    3) Embed rows in a batch.
    4) Upsert into Qdrant with those payloads.
    Returns: { "ingested_count": <number_of_rows> }.
    """

    # 1) Wrap bytes in BytesIO
    if isinstance(file_bytes, (bytes, bytearray)):
        csv_stream = io.BytesIO(file_bytes)
    elif isinstance(file_bytes, io.BytesIO):
        csv_stream = file_bytes
    else:
        raise ValueError("handle_csv_v2 expects raw bytes or io.BytesIO")

    # 2) Load CSV
    try:
        df = pd.read_csv(csv_stream)
    except Exception as e:
        logger.error(f"[handle_csv_v2] Failed to read CSV: {e}")
        raise

    if df.empty:
        raise ValueError("CSV is empty or unreadable")

    # 3) Build texts + metadata
    texts = []
    metadatas = []
    for idx, row in df.iterrows():
        row_text = " ".join(str(val) for val in row.values if pd.notna(val))
        texts.append(row_text)
        metadatas.append({
            "row_index": int(idx),
            "file_name": file_name
        })

    # 4) Batch‐embed
    try:
        embeddings = embeddings_model_large.embed_documents(texts)
    except Exception as e:
        logger.error(f"[handle_csv_v2] Embedding failed: {e}")
        raise

    # 5) Ensure Qdrant collection exists
    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    collection_name = settings.CSV_COLLECTION

    try:
        client.get_collection(collection_name=collection_name)
    except Exception:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )

    # 6) Build and upsert PointStructs
    points = []
    for i, emb in enumerate(embeddings):
        point_id = str(uuid.uuid4())
        points.append(
            PointStruct(
                id=point_id,
                vector=emb,
                payload=metadatas[i]
            )
        )

    try:
        client.upsert(collection_name=collection_name, points=points)
    except Exception as e:
        logger.error(f"[handle_csv_v2] Qdrant upsert failed: {e}")
        raise

    ingested_count = len(points)
    logger.info(f"[handle_csv_v2] Ingested {ingested_count} rows into '{collection_name}'")
    return {"ingested_count": ingested_count}
