# Import necessary libraries
import streamlit as st
from streamlit_chat import message
import tempfile
from langchain_community.document_loaders import CSVLoader
from langchain.chains import ConversationalRetrievalChain
from model_management import  llm_chat, embeddings_model_large
from hashlib import sha256
from qdrant_client.models import VectorParams, Distance
from langchain.vectorstores import Qdrant
from langchain.docstore.document import Document
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue


# Initialize Qdrant client with API key
API_KEY = "EQPJd8M3SDDY2fpPUU7nWcWvtjwJw5YkzdgP4gCJlCrKxPNk_COSuQ"


client = QdrantClient(
    url="https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",
    api_key=API_KEY)

# COLLECTION_NAME_CSV = "buildsmart-csv-collection"

COLLECTION_NAME_CSV = "buildsmart-csv-collection"


def csv_qdrant_hybrid_retriever(chunks, column_contents, document_name):
    """
    Stores chunks and CSV column contents in Qdrant vector store with associated metadata.
    """
    client = QdrantClient(
        url="https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",
        api_key=API_KEY
    )
    existing_collections = client.get_collections().collections
    collection_names = [col.name for col in existing_collections]
    if COLLECTION_NAME_CSV not in collection_names:
        client.recreate_collection(
            collection_name=COLLECTION_NAME_CSV,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
            # vectors_config = VectorParams(size=500, distance=Distance.COSINE)
        )

    # documents = chunks + [Document(page_content=text, metadata={"column": col}) for col, text in column_contents.items()]

    # Step 1: Retrieve existing document names
    existing_docs, _ = client.scroll(COLLECTION_NAME_CSV, limit=10)
    existing_names = {doc.payload['metadata'].get("document_name", "").strip() for doc in existing_docs}
    # print(f"📂 Existing document names: {existing_names}")
    if document_name in existing_names:
        print(f"🚫 Document '{document_name}' already exists. Skipping insertion.")

    for doc in chunks:
        doc.metadata["document_name"] = document_name

    documents = chunks + [
        Document(page_content=str(text) if text is not None else "", metadata={"column": col})
        for col, text in column_contents.items()
    ]

    db = Qdrant.from_documents(
        documents=documents,
        embedding=embeddings_model_large,
        url="https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",
        api_key=API_KEY,
        collection_name=COLLECTION_NAME_CSV,
        prefer_grpc=True,
        timeout = 60
    )
    retriever = db.as_retriever()

    return retriever



def initialize_chain_csv(llm, retriever):
    """Initialize the conversational chain using hybrid retrieval."""
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
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
    loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8", csv_args={'delimiter': ','})
    data = loader.load()
    if not data:
        st.error("No data found in the CSV.")
        return
    # column_contents = {col: " ".join([row[col] for row in data]) for col in data[0].keys()}

    column_contents = {}
    for doc in data:
        for key, value in doc.metadata.items():  # Extract metadata fields
            column_contents.setdefault(key, []).append(str(value))  # Ensure it's a string
        column_contents.setdefault("content", []).append(doc.page_content)  # Store main text content
    column_contents = {col: " ".join(values) for col, values in column_contents.items()}
    # print('uploaded file names ...', uploaded_file.name)

    # retriever = csv_qdrant_hybrid_retriever(data, column_contents)
    retriever = csv_qdrant_hybrid_retriever(data, column_contents, uploaded_file.name)
    # print('retriever here..', retriever)

    chain = initialize_chain_csv(llm_chat, retriever)
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'generated' not in st.session_state:
        st.session_state['generated'] = [f"Hello! Ask me about {uploaded_file.name} 🤗"]
    if 'past' not in st.session_state:
        st.session_state['past'] = ["Hey! 👋"]
    response_container = st.container()
    container = st.container()
    with container:
        with st.form(key='my_form', clear_on_submit=True):
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
