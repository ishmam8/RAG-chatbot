
# Import necessary libraries
from streamlit_chat import message
from model_management import embeddings_model, llm_chat  # Ensure 'embeddings' and 'llm' are initialized
import tempfile
from langchain.document_loaders import CSVLoader
import streamlit as st
from langchain.chains import ConversationalRetrievalChain
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_community.vectorstores import Qdrant



# Initialize Qdrant client with API key
API_KEY = "EQPJd8M3SDDY2fpPUU7nWcWvtjwJw5YkzdgP4gCJlCrKxPNk_COSuQ"  # Replace with your actual API key


client = QdrantClient(
    url="https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",  # Replace with your Qdrant instance URL
    api_key=API_KEY)


COLLECTION_NAME_csv = "buildsmart-csv-collection"


def csv_qdrant_retriever(chunks):
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

    if COLLECTION_NAME_csv not in collection_names:
        client.recreate_collection(
            collection_name=COLLECTION_NAME_csv,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)  # Adjust size based on embedding model
        )

    # Initialize Qdrant vector store
    db = Qdrant.from_documents(
        documents=chunks,
        embedding=embeddings_model,
        url = "https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",
        api_key=API_KEY,
        collection_name=COLLECTION_NAME_csv,
        prefer_grpc=True
    )

    # Create a Retriever for querying
    retriever = db.as_retriever()

    return retriever



def initialize_chain_csv(llm, retriever):
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


def handle_csv_v2(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    # Load CSV data using CSVLoader
    loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8", csv_args={'delimiter': ','})
    data = loader.load()

    if not data:
        st.error("No data found in the CSV.")
        return

    retriever = csv_qdrant_retriever(data)

    # Initialize the conversational chain
    chain = initialize_chain_csv(llm_chat, retriever)

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
            user_input = st.text_input("Query:", placeholder="Ask me about the CSV 👉", key='input')
            submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            output = conversational_chat(user_input, chain)
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(output)

    # Display chat history
    if st.session_state['generated']:
        with response_container:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state["past"][i], is_user=True, key=f"{i}_user", avatar_style="big-smile")
                message(st.session_state["generated"][i], key=str(i), avatar_style="thumbs")
