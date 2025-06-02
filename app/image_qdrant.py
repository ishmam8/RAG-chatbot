

# Import necessary libraries
import streamlit as st
from streamlit_chat import message
import tempfile
import io
import os
from PIL import Image
import torch
import torchvision.transforms as transforms
from torchvision import models
import numpy as np
from langchain_community.document_loaders import CSVLoader
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
# Import custom modules/functions
from model_management import embeddings_model, llm_chat
from langchain.docstore.document import Document
from database import vector_store, delete_vector_store, inspect_vector_store

# Initialize Qdrant client with API key
API_KEY = "YOUR_QDRANT_API_KEY"  # Replace with your actual API key
QDRANT_URL = "YOUR_QDRANT_URL"  # Replace with your actual Qdrant URL
COLLECTION_NAME_CSV = "buildsmart-csv-collection"
COLLECTION_NAME_IMAGES = "buildsmart-image-collection"

client = QdrantClient(url=QDRANT_URL, api_key=API_KEY)

# Load pre-trained model for image feature extraction
resnet_model = models.resnet50(pretrained=True)
resnet_model.eval()  # Set to evaluation mode

# Define Image Preprocessing
def preprocess_image(image):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Resize to match ResNet input size
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    return transform(image).unsqueeze(0)  # Add batch dimension

# Extract feature embeddings from images
def extract_features(image):
    image_tensor = preprocess_image(image)
    with torch.no_grad():
        features = resnet_model(image_tensor)
    return features.squeeze().numpy()  # Convert to NumPy array


# Store image embeddings in Qdrant
def store_image_embeddings(image_name, image_embedding):
    client.upsert(
        collection_name=COLLECTION_NAME_IMAGES,
        points=[
            PointStruct(
                id=hash(image_name),  # Use image name hash as ID
                vector=image_embedding.tolist(),
                payload={"image_name": image_name}
            )
        ]
    )



def initialize_chain_image(llm, retriever):
    """Initialize the conversational chain using the given retriever."""

    # Ensure Qdrant retriever is properly loaded
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,  # Use the pre-configured Qdrant retriever
        return_source_documents=True
    )

    return chain



def image_qdrant_retriever(chunks):
    """
    Stores chunks in a Qdrant vector store with associated metadata.

    Args:
        chunks (List[Document]): The list of Document objects to store.
        embeddings: The embeddings model to use.
        collection_name (str): Qdrant collection name.
        url (str): Qdrant URL.
        api_key (str): API key for authentication.

    Returns:
        Qdrant: The Qdrant vector store instance.
    """

    client = QdrantClient(
        url="https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",
        api_key=API_KEY
    )

    # Check if the collection exists, if not, create it
    existing_collections = client.get_collections().collections
    collection_names = [col.name for col in existing_collections]

    if COLLECTION_NAME_IMAGES not in collection_names:
        client.recreate_collection(
            collection_name=COLLECTION_NAME_IMAGES,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)  # Adjust size based on embedding model
        )

    # Initialize Qdrant vector store
    db = Qdrant.from_documents(
        documents=chunks,
        embedding=embeddings_model,
        url = "https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",
        api_key=API_KEY,
        collection_name=COLLECTION_NAME_IMAGES,
        prefer_grpc=True
    )

    # Create a Retriever for querying
    retriever = db.as_retriever()

    return retriever


def conversational_chat(user_input, chain):
    """
    Processes user input through the conversational chain and returns the response with page references and metadata.

    Args:
        user_input (str): The user's query.
        chain: The ConversationalRetrievalChain instance.

    Returns:
        str: The response from the chatbot, including page references and metadata.
    """
    # Process user input through the chain
    result = chain({"question": user_input, "chat_history": st.session_state.get('history', [])})

    # Extract the answer and source documents
    answer = result.get('answer', "I'm not sure about that.")
    source_docs = result.get('source_documents', [])

    # Extract and format metadata from source documents
    metadata_info = set()
    for doc in source_docs:
        page_number = doc.metadata.get("Page")
        file_name = doc.metadata.get("File")  # Assuming 'File' key exists in metadata
        if page_number and file_name:
            metadata_info.add(f"[File: {file_name}, Page {page_number}]")

    # Append metadata sources to the answer
    if metadata_info:
        answer += f" (Sources: {'; '.join(metadata_info)})"

    # Update chat history
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    st.session_state['history'].append((user_input, answer))

    return answer


# Handle Image Upload
def handle_image_upload(uploaded_file):
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    # Extract features
    image_features = extract_features(image)
    store_image_embeddings(uploaded_file.name, image_features)

    st.success(f"Image '{uploaded_file.name}' processed and stored successfully!")


# Handle CSV Upload
def handle_image(uploaded_file):
    image = Image.open(uploaded_file)

    data = image

    if not data:
        st.error("No data found in the CSV.")
        return

    retriever = image_qdrant_retriever(data)
    chain = initialize_chain_image(llm_chat, retriever)

    # Initialize chat history
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'generated' not in st.session_state:
        st.session_state['generated'] = [f"Hello! Ask me about {uploaded_file.name} 🤗"]
    if 'past' not in st.session_state:
        st.session_state['past'] = ["Hey! 👋"]

    # Chat Interface
    response_container = st.container()
    container = st.container()

    with container:
        with st.form(key='csv_form', clear_on_submit=True):
            user_input = st.text_input("Query:", placeholder="Ask me about the CSV 👉", key='input')
            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            output = conversational_chat(user_input, chain)
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(output)

    if st.session_state['generated']:
        with response_container:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state["past"][i], is_user=True, key=f"{i}_user", avatar_style="big-smile")
                message(st.session_state["generated"][i], key=str(i), avatar_style="thumbs")