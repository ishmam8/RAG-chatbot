
# Import necessary libraries
import streamlit as st
from streamlit_chat import message
import tempfile
import io
from langchain_community.document_loaders import CSVLoader
from PyPDF2 import PdfReader
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import OpenAIEmbeddings  # Or HuggingFaceEmbeddings if preferred
from langchain.vectorstores import FAISS
from langchain.llms import OpenAI  # Adjust based on your LLM provider
# Import your custom modules/functions
from pdf_prepro import get_chunks, pdf_read_2, vector_store_txt  # Ensure this function is properly defined
from model_management import embeddings, llm  # Ensure 'embeddings' and 'llm' are initialized
from langchain.docstore.document import Document
import os
from database import vector_store, delete_vector_store, inspect_vector_store
from pdf_prepro import get_chunks_with_page_numbers
from langchain.vectorstores import FAISS


from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import os

import os
import tempfile
import qdrant_client
from qdrant_client.models import PointStruct, Distance, VectorParams, Filter
from langchain.vectorstores import Qdrant
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain.document_loaders import CSVLoader
import streamlit as st

# Initialize Qdrant client with API key
API_KEY = "EQPJd8M3SDDY2fpPUU7nWcWvtjwJw5YkzdgP4gCJlCrKxPNk_COSuQ"  # Replace with your actual API key

client = QdrantClient(
    url="https://211d825e-4982-469e-8f5b-fef71a5bc1f7.eu-west-1-0.aws.cloud.qdrant.io",  # Replace with your Qdrant instance URL
    api_key=API_KEY
)

COLLECTION_NAME = "buildsmart_collection"


def initialize_qdrant_collection(embedding_dim=3072):
    """
    Initialize the Qdrant collection if it doesn't exist.
    """
    existing_collections = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing_collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
        )
        print(f"Collection '{COLLECTION_NAME}' created.")
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists.")



def vector_store_qdrant(chunks, embeddings):
    """
    Stores document embeddings in Qdrant.

    Args:
        chunks (List[Document]): The list of Document objects.
        embeddings: The embeddings model.
    """
    # Filter out empty documents
    # valid_chunks = [chunk for chunk in chunks if chunk.page_content and isinstance(chunk.page_content, str)]

    valid_chunks = [
        chunk for chunk in chunks
        if isinstance(chunk.page_content, str) and chunk.page_content.strip()
    ]

    if not valid_chunks:
        print("No valid chunks to store in Qdrant.")
        return

    vectors = [embeddings.embed_query(chunk.page_content) for chunk in valid_chunks]
    payloads = [{"text": chunk.page_content} for chunk in valid_chunks]

    points = [
        PointStruct(id=i, vector=vectors[i], payload=payloads[i])
        for i in range(len(valid_chunks))
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Inserted {len(valid_chunks)} documents into Qdrant.")





def initialize_chain_qdrant(embeddings, llm):
    """
    Initializes the ConversationalRetrievalChain with Qdrant.

    Args:
        embeddings: The embeddings model.
        llm: The language model instance.

    Returns:
        ConversationalRetrievalChain: The initialized conversational chain.
    """
    retriever = Qdrant(
        client=client,
        collection_name=COLLECTION_NAME,
        embeddings=embeddings
    ).as_retriever()

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    return chain


def conversational_chat_csv(user_input, chain):
    """
    Processes user input through the conversational chain and returns the response
    with page references and metadata from Qdrant.

    Args:
        user_input (str): The user's query.
        chain: The ConversationalRetrievalChain instance.

    Returns:
        str: The response from the chatbot, including page references and metadata.
    """
    # Process user input through the retrieval chain
    result = chain({"question": user_input, "chat_history": st.session_state['history']})

    # Extract answer and source documents
    answer = result.get('answer', "I'm not sure, could you rephrase that?")
    source_docs = result.get('source_documents', [])

    # Filter out documents with missing page_content
    filtered_docs = [
        doc for doc in source_docs
        if doc.page_content and isinstance(doc.page_content, str) and doc.page_content.strip()
    ]

    # Extract metadata
    metadata_info = set()

    for doc in filtered_docs:
        # metadata = doc.metadata if hasattr(doc, "metadata") else {}
        # Ensure doc.metadata is a valid dictionary
        metadata = doc.metadata if isinstance(doc.metadata, dict) else {}

        page_number = metadata.get("Page") or metadata.get("page")
        file_name = metadata.get("File") or metadata.get("file")

        if file_name and page_number:
            metadata_info.add(f"[File: {file_name}, Page {page_number}]")

    # Append metadata sources to answer
    if metadata_info:
        sources = "; ".join(metadata_info)
        answer += f" (Sources: {sources})"

    # Update chat history
    st.session_state['history'].append((user_input, answer))

    return answer


def handle_csv2(uploaded_file):

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    # Load CSV data using CSVLoader
    loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8", csv_args={'delimiter': ','})

    # data = loader.load()
    # if not data:
    #     st.error("No data found in the CSV.")
    #     return
    data = loader.load()

    # Ensure all documents have valid text
    data = [doc for doc in data if isinstance(doc.page_content, str) and doc.page_content.strip()]

    if not data:
        st.error("No valid data found in the CSV.")
        return

    # Initialize Qdrant collection
    initialize_qdrant_collection()


    # Store embeddings in Qdrant
    vector_store_qdrant(data, embeddings)

    # Initialize the conversational chain
    chain = initialize_chain_qdrant(embeddings, llm)

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
            output = conversational_chat_csv(user_input, chain)
            st.session_state['past'].append(user_input)
            st.session_state['generated'].append(output)

    # Display chat history
    if st.session_state['generated']:
        with response_container:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state["past"][i], is_user=True, key=f"{i}_user", avatar_style="big-smile")
                message(st.session_state["generated"][i], key=str(i), avatar_style="thumbs")


# def conversational_chat_csv(user_input, chain):
#     """
#     Processes user input through the conversational chain and returns the response
#     with page references and metadata from Qdrant.
#
#     Args:
#         user_input (str): The user's query.
#         chain: The ConversationalRetrievalChain instance.
#
#     Returns:
#         str: The response from the chatbot, including page references and metadata.
#     """
#     # Process user input through the retrieval chain
#     result = chain({"question": user_input, "chat_history": st.session_state['history']})
#
#     # Extract the answer and source documents
#     answer = result.get('answer', "I'm not sure, could you rephrase that?")
#     source_docs = result.get('source_documents', [])
#
#     # Extract metadata from source documents
#     metadata_info = set()  # Using a set to avoid duplicates
#
#     for doc in source_docs:
#         metadata = doc.metadata if hasattr(doc, "metadata") else {}
#         page_number = metadata.get("Page") or metadata.get("page")  # Case-insensitive handling
#         file_name = metadata.get("File") or metadata.get("file")
#
#         if file_name and page_number:
#             metadata_info.add(f"[File: {file_name}, Page {page_number}]")
#
#     # Append metadata sources to answer
#     if metadata_info:
#         sources = "; ".join(metadata_info)
#         answer += f" (Sources: {sources})"
#
#     # Update chat history
#     st.session_state['history'].append((user_input, answer))
#
#     return answer



 # # Load CSV data using CSVLoader
 #    loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8", csv_args={'delimiter': ','})
 #    data = loader.load()
 #
 #    if not data:
 #        st.error("No data found in the CSV.")
 #        return
 #
 #    # Initialize Qdrant collection
 #    initialize_qdrant_collection()
 #
 #
 #    # Store embeddings in Qdrant
 #    vector_store_qdrant(data, embeddings)
 #
 #    # Initialize the conversational chain
 #    chain = initialize_chain_qdrant(embeddings, llm)




# def initialize_chain(db_path, embeddings, llm):
#     """
#     Initializes the ConversationalRetrievalChain.
#
#     Args:
#         db_path (str): Path to the FAISS vector store.
#         embeddings: The embeddings model to use.
#         llm: The language model instance.
#
#     Returns:
#         ConversationalRetrievalChain: The initialized conversational chain.
#     """
#     # Load the vector store with dangerous deserialization allowed
#     db = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
#
#     # Initialize the ConversationalRetrievalChain
#     chain = ConversationalRetrievalChain.from_llm(
#         llm=llm,
#         retriever=db.as_retriever(),
#         return_source_documents=True  # Ensure source documents are returned
#     )
#
#     return chain


# def vector_store_csv(chunks, embeddings, db_path="faiss_db"):
#     """
#     Stores chunks in a FAISS vector store with associated metadata.
#
#     Args:
#         chunks (List[Document]): The list of Document objects to store.
#         embeddings: The embeddings model to use.
#         db_path (str): Path to save/load the FAISS index.
#     Returns:
#         FAISS: The FAISS vector store instance.
#     """
#     # Initialize FAISS vector store with embeddings
#     db = FAISS.from_documents(chunks, embeddings)
#     db.save_local(db_path)
#     return db


def handle_csv(uploaded_file, db_path):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    # Load CSV data using CSVLoader
    loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8", csv_args={'delimiter': ','})
    data = loader.load()

    if not data:
        st.error("No data found in the CSV.")
        return

    # Create a FAISS vector store and save embeddings
    db = vector_store_csv(data, embeddings, db_path=db_path)

    # Initialize the conversational chain
    chain = initialize_chain(db_path, embeddings, llm)

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
