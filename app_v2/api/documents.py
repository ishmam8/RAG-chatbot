from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from botocore.exceptions import BotoCoreError
import boto3

from langchain_community.embeddings import OpenAIEmbeddings

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from app_v2.config import settings
from app_v2.utils.pdf_faiss import handle_pdf  
from app_v2.utils.csv_faiss import handle_csv
from app_v2.core.auth import get_current_user
from app_v2.schemas import FileUploadResponse  

router = APIRouter(tags=["documents"])

#TODO:
# Make this route admin only
@router.post("/upload", response_model=FileUploadResponse)
async def upload_document(
    project_id: str = Form(..., description="ID of the project to ingest into"),
    file: UploadFile = File(...), current_user: str = Depends(get_current_user)):
    """
    Endpoint to upload a PDF or CSV, chunk/embed it, and store in FAISS.
    """
    filename = file.filename.lower()
    if not (filename.endswith(".pdf") or filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Only PDF or CSV allowed.")

    await file.seek(0)
    file_content_bytes = await file.read()

    #TODO:
    # 1) Upload to S3 (if desired—mirrors Streamlit’s behavior)
    # s3 = boto3.client(
    #     "s3",
    #     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    #     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    #     region_name="us-east-2"
    # )
    # try:
    #     await file.seek(0)  # Ensure pointer at start
    #     s3.upload_fileobj(await file.read(), settings.BUCKET_NAME, file.filename)
    # except BotoCoreError as e:
    #     raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")
    

    # 3) Call the existing ingestion routines
    if filename.endswith(".pdf"):
        result = handle_pdf(project_id, file_content_bytes, file_name=file.filename)
    else:
        result = handle_csv(project_id, file, file_name=file.filename)

    return {"detail": f"'{file.filename}' ingested into project '{project_id}' ({result['ingested_count']} chunks).", 
            "project_id": project_id}
