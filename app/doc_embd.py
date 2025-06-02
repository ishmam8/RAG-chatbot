
import sys
import tempfile
from langchain_community.document_loaders import CSVLoader
from csv_qdrant2 import csv_qdrant_hybrid_retriever
import streamlit as st


def save_csv_embedding(uploaded_file):
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

  retriever = csv_qdrant_hybrid_retriever(data, column_contents, uploaded_file.name)
  print("save csv embedding into Vector Database Successfully...")


if __name__ == "__main__":
  csv_uploading = sys.argv[1]
  save_csv_embedding(csv_uploading)

  print("save csv embedding file into vector database ...")