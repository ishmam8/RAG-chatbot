
import os
from langchain_community.vectorstores import FAISS
# from model_management import embeddings_model_large, llm_chat
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Tuple
from langchain.vectorstores import FAISS
# from langchain.embeddings import Embeddings
from langchain.docstore.document import Document
######  PDF file preprocessing ##########


def get_chunks_with_page_numbers(text, page_number, chunk_size=500, overlap=50):
    """
    Splits text into chunks with associated page numbers.
    Args:
        text (str): The text to split.
        page_number (int): The page number from which the text is extracted.
        chunk_size (int): The maximum size of each chunk.
        overlap (int): The number of overlapping characters between chunks.

    Returns:
        List[Document]: A list of Document objects with content and metadata.
    """
    chunks = []
    # Split text into chunks based on chunk_size and overlap
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk.strip():  # Avoid adding empty chunks
            doc = Document(
                page_content=chunk,
                metadata={"page_number": page_number}
            )
            chunks.append(doc)
    return chunks


def pdf_read(pdf_doc):
    text = ""
    for pdf in pdf_doc:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


# def vector_store(text_chunks):
#     vector_store = FAISS.from_texts(text_chunks, embedding=embeddings_model_large)
#     vector_store.save_local("faiss_db")


def pdf_read_2(pdf, file_name_str: str):
    text_with_metadata = []
    pdf_reader = PdfReader(pdf)
    for page_number, page in enumerate(pdf_reader.pages, start=1):
        page_text = page.extract_text()
        if page_text:  # Ensure the page contains text
            #metadata = f"[File: {pdf.name}, Page {page_number}]"
            metadata = {"File": file_name_str, "Page": page_number}
            # print('reading pdf meta data...', metadata)
            text_with_metadata.append((metadata, page_text))

    return text_with_metadata


def get_chunks(text_with_metadata):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = []
    for metadata, text in text_with_metadata:
        split_texts = text_splitter.split_text(text)
        for split in split_texts:
            chunks.append((metadata, split))  # Attach metadata to each chunk
    # print('chunks ...', chunks)
    return chunks


def load_existing_vector_store(db_path, embeddings):
    """Load an existing vector store if it exists; otherwise, create a new one."""
    if os.path.exists(db_path):
        return FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    return FAISS.from_documents([],  embedding=embeddings)  # Create a new, empty vector store


def vector_store_txt(text_chunks, embeddings, db_path):
    # documents = [f"{metadata}\n{text}" for metadata, text in text_chunks]
    documents = []
    for metadata, text in text_chunks:
        doc = Document(page_content=text,metadata =metadata)
        # print('each doc update ...', doc )
        documents.append(doc)
    # print('adding documents ...',documents)
    if os.path.exists(db_path):
        vector_store = load_existing_vector_store(db_path, embeddings)
        # new_store = FAISS.from_texts(documents, embedding=embeddings)
        new_store = FAISS.from_documents(documents, embedding=embeddings)
        vector_store.merge_from(new_store)
        vector_store.save_local(db_path)
    else:
        # new_store = FAISS.from_texts(documents, embedding=embeddings)
        new_store = FAISS.from_documents(documents, embedding=embeddings)
        new_store.save_local(db_path)


# def get_chunks(text):
#     text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#     chunks = text_splitter.split_text(text)
#     # print('chunks ....', chunks)
#     return chunks


# def vector_store_txt(text_chunks, embeddings, db_path):
#     """
#     Updates a vector store by removing old embedded files and adding new ones.
#
#     Parameters:
#     - text_chunks: List of tuples, where each tuple contains metadata and text.
#     - embeddings: Embedding model to create vector representations.
#     - db_path: Path to the existing FAISS vector store.
#
#     Returns:
#     None
#     """
#     # Combine metadata and text for each chunk
#     documents = [f"{metadata}\n{text}" for metadata, text in text_chunks]
#
#     # Load the existing vector store
#     vector_store = load_existing_vector_store(db_path, embeddings)
#
#     # Filter out documents that are already in the store
#     existing_documents = vector_store.get_all_texts()
#     updated_documents = [doc for doc in documents if doc not in existing_documents]
#
#     # Remove old documents (if needed, based on some metadata criteria)
#     # For example, remove documents with matching metadata
#     old_metadata = [metadata for metadata, _ in text_chunks]
#     vector_store.remove_by_metadata(old_metadata)
#
#     # Add new/updated documents
#     if updated_documents:
#         new_store = FAISS.from_texts(updated_documents, embedding=embeddings)
#         vector_store.merge_from(new_store)
#
#     # Save updated vector store
#     vector_store.save_local(db_path)