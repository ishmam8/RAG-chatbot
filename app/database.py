# database.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import shutil
import os
from langchain.vectorstores import FAISS

# Initialize the database engine
engine = create_engine('sqlite:///users.db', echo=True)

# Create a base class for declarative class definitions
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)

# Create the users table
Base.metadata.create_all(engine)

# Create a session factory
SessionLocal = sessionmaker(bind=engine)


def delete_vector_store(db_path):
    """Delete the entire local vector store."""
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        print(f"Vector store at '{db_path}' has been deleted.")
    else:
        print(f"Vector store at '{db_path}' does not exist.")

def inspect_vector_store(db_path, embeddings):
    """Check the contents of the vector store."""
    if not os.path.exists(db_path):
        return "The vector store does not exist."

    try:
        # Load the vector store
        vector_store = FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)

        # Inspect metadata and text chunks
        elements = vector_store.docstore._dict  # Access stored documents
        print(f"Number of documents: {len(elements)}")

        for doc_id, doc in elements.items():
            print(f"Document ID: {doc_id}")
            print(f"Metadata: {doc.metadata}")
            print(f"Content: {doc.page_content[:100]}...")  # Show first 100 characters

        return f"Vector store contains {len(elements)} documents."
    except Exception as e:
        return f"Error inspecting vector store: {e}"



def vector_store(chunks, embeddings, db_path="faiss_db"):
    """
    Stores chunks in a FAISS vector store with associated metadata.

    Args:
        chunks (List[Document]): The list of Document objects to store.
        embeddings: The embeddings model to use.
        db_path (str): Path to save/load the FAISS index.
    Returns:
        FAISS: The FAISS vector store instance.
    """
    # Initialize FAISS vector store with embeddings
    db = FAISS.from_documents(chunks, embeddings)
    db.save_local(db_path)
    return db