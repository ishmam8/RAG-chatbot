
# Import necessary libraries
from streamlit_chat import message
from pdf_prepro import get_chunks, pdf_read_2, vector_store_txt  # Ensure this function is properly defined
from model_management import embeddings_model, llm_chat  # Ensure 'embeddings' and 'llm' are initialized
from langchain.docstore.document import Document
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter
import streamlit as st
from qdrant_client import QdrantClient
from langchain.vectorstores import Qdrant
from langchain.chains import ConversationalRetrievalChain



# Initialize Qdrant client with API key
API_KEY = "EQPJd8M3SDDY2fpPUU7nWcWvtjwJw5YkzdgP4gCJlCrKxPNk_COSuQ"  # Replace with your actual API key


client = QdrantClient(
    url="https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",  # Replace with your Qdrant instance URL
    api_key=API_KEY
)


COLLECTION_NAME = "buildsmart-pdf-collection"



def load_existing_vector_store_qdrant():
    """Load an existing vector store from Qdrant."""
    try:
        collection = client.get_collection(collection_name=COLLECTION_NAME)
        return collection
    except Exception as e:
        print(f"Collection not found: {e}")
        return None


def qdrant_retriever(text_chunks):

    # Qdrant client initialization
    client = QdrantClient(
        url="https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",
        api_key=API_KEY
    )

    # Check if collection exists
    collections = client.get_collections().collections
    existing_collections = {col.name for col in collections}
    # print('existing collections ...', existing_collections)

    if COLLECTION_NAME not in existing_collections:
        print(f"Collection '{COLLECTION_NAME}' not found. Creating a new one...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)  # Adjust size as per embedding model
        )

    # Convert tuples (metadata, text) into Document objects
    documents = [Document(page_content=text, metadata=metadata) for metadata, text in text_chunks]

    # Initialize Qdrant with Remote Storage
    vectordb = Qdrant.from_documents(
        documents=documents,
        embedding=embeddings_model,
        # location=client,  # Use the remote client instead of ":memory:"
        url = "https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",
        api_key=API_KEY,
        prefer_grpc=True,
        collection_name=COLLECTION_NAME,
    )

    # Create a Retriever for querying
    retriever = vectordb.as_retriever()

    return retriever



def initialize_chain_pdf(llm, retriever):
    """Initialize the conversational chain using the given retriever."""

    # Ensure Qdrant retriever is properly loaded
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,  # Use the pre-configured Qdrant retriever
        return_source_documents=True
    )

    return chain


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


def handle_pdf_3(uploaded_file):
    # Read the uploaded PDF
    raw_text = pdf_read_2(uploaded_file)
    text_chunks = get_chunks(raw_text)

    # Store chunks in the vector store
    retriever = qdrant_retriever(text_chunks)

    # Initialize the conversational chain
    chain = initialize_chain_pdf(llm_chat, retriever)

    # Initialize chat history
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    # Initialize messages
    if 'generated' not in st.session_state:
        st.session_state['generated'] = [f"Hello! Ask me about {uploaded_file.name} 🤗"]
    if 'past' not in st.session_state:
        st.session_state['past'] = ["Hey! 👋"]

    # Create containers for chat history and user input
    response_container = st.container()
    container = st.container()

    # User input form
    with container:
        with st.form(key='my_form', clear_on_submit=True):
            user_input = st.text_input("Query:", placeholder="Ask me about the PDF 👉", key='input')
            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            output = conversational_chat(user_input, chain)
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(output)

    # Display chat history
    if st.session_state['generated']:
        with response_container:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state["past"][i], is_user=True, key=f"{i}_user", avatar_style="fun-emoji")
                message(st.session_state["generated"][i], key=str(i), avatar_style="bottts")