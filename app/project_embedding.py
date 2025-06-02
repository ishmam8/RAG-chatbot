import sys
from langchain.vectorstores import Qdrant
from langchain.docstore.document import Document
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.models import VectorParams, Distance
from model_management import  llm_chat, embeddings_model_large

# Initialize Qdrant client with API key
API_KEY = QDRANT_CLIENT_API_KEY


client = QdrantClient(
    url=QDRANT_CLIENT_URL,
    api_key=API_KEY)

# COLLECTION_NAME_CSV = "buildsmart-csv-collection"

COLLECTION_NAME_project = "buildsmart-project-collection"


def qdrant_project_retriever(project_name, project_intro):
    """
    Embeds and stores project name and project introduction in Qdrant vector DB with metadata.
    Returns a retriever for querying.
    """
    client = QdrantClient(
        url="https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",
        api_key=API_KEY
    )

    # Create collection if it doesn't exist
    existing_collections = client.get_collections().collections
    collection_names = [col.name for col in existing_collections]
    if COLLECTION_NAME_project not in collection_names:
        client.recreate_collection(
            collection_name=COLLECTION_NAME_project,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
        )

    # Check for existing project
    existing_docs, _ = client.scroll(COLLECTION_NAME_project, limit=100)
    existing_names = {doc.payload['metadata'].get("project_name", "").strip() for doc in existing_docs}
    if project_name in existing_names:
        print(f"🚫 Project '{project_name}' already exists. Skipping insertion.")
        return Qdrant(
            client=client,
            collection_name=COLLECTION_NAME_project,
            embedding_function=embeddings_model_large
        ).as_retriever()

    # Prepare documents
    documents = [
        Document(
            page_content=project_name,
            metadata={"type": "project_name", "project_name": project_name}
        ),
        Document(
            page_content=project_intro,
            metadata={"type": "project_intro", "project_name": project_name}
        )
    ]

    # Store in Qdrant
    db = Qdrant.from_documents(
        documents=documents,
        embedding=embeddings_model_large,
        url="https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",
        api_key=API_KEY,
        collection_name=COLLECTION_NAME_project,
        prefer_grpc=True,
        timeout=60
    )

    retriever = db.as_retriever()
    return retriever

if __name__ == "__main__":
  project_name = sys.argv[1]
  project_intro = sys.argv[1]
  qdrant_project_retriever(project_name, project_intro)

  print("save project embedding file into vector database ...")