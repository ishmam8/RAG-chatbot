
# Import necessary libraries
import streamlit as st
import io
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores import FAISS
from pdf_qdrant_2 import handle_pdf_3
from csv_qdrant2 import handle_csv_v2
import boto3



# Load credentials from Streamlit secrets
s3 = boto3.client(
    "s3",
    aws_access_key_id="access_key_id",
    aws_secret_access_key="access_secret_key",
    region_name="us-east-2",
)

BUCKET_NAME = "smart-buildr-s3"


def initialize_chain(db_path, embeddings_model, llm):
    """
    Initializes the ConversationalRetrievalChain.

    Args:
        db_path (str): Path to the FAISS vector store.
        embeddings: The embeddings model to use.
        llm: The language model instance.

    Returns:
        ConversationalRetrievalChain: The initialized conversational chain.
    """
    # Load the vector store with dangerous deserialization allowed
    db = FAISS.load_local(db_path, embeddings_model, allow_dangerous_deserialization=True)
    # Initialize the ConversationalRetrievalChain
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=db.as_retriever(),
        return_source_documents=True  # Ensure source documents are returned
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
    # Process the user input through the chain
    result = chain({"question": user_input, "chat_history": st.session_state['history']})
    # Extract the answer and source documents
    answer = result['answer']
    source_docs = result.get('source_documents', [])

    # Extract and format metadata from source documents
    metadata_info = []
    for doc in source_docs:
        page_number = doc.metadata.get("Page")
        file_name = doc.metadata.get("File")  # Assuming 'file_name' is included in metadata
        if page_number and file_name:
            # metadata_info.append(f"[File: {file_name}, Page {page_number}]")
            comp_name_number = f"[File: {file_name}, Page {page_number}]"
            if comp_name_number not in metadata_info:
                metadata_info.append(f"[File: {file_name}, Page {page_number}]")

    # Add metadata to the answer
    if metadata_info:
        sources = "; ".join(metadata_info)
        answer += f" (Sources: {sources})"

    # Update chat history
    st.session_state['history'].append((user_input, answer))

    return answer



def chat_interface_total(uploaded_file):
    # Handle CSV and PDF uploads
    if uploaded_file:
        # Read the file into memory
        file_bytes = uploaded_file.read()
        file_copy = io.BytesIO(file_bytes)  # Create a copy to use for processing
        file_copy.seek(0)  # Reset pointer
        # Upload to S3
        s3.upload_fileobj(io.BytesIO(file_bytes), BUCKET_NAME, uploaded_file.name)
        # st.success(f"File '{uploaded_file.name}' uploaded successfully to S3!")

        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension == 'csv':
            # handle_csv(uploaded_file, DB_FAISS_PATH)
            handle_csv_v2(uploaded_file)
        elif file_extension == 'pdf':
            # handle_pdf_2(uploaded_file, DB_FAISS_PATH)
            handle_pdf_3(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload a CSV or PDF file.")







