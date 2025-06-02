# # Use the official Python 3.10 image as the base
# FROM python:3.10-slim
#
# # Set the working directory in the container
# WORKDIR /app
#
# # Copy the requirements.txt to the container
# COPY ./requirements.txt /app/requirements.txt
#
# # Install dependencies from requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt
#
# # Copy the entire app into the working directory
# COPY ./app /app
#
# # Expose port 8501 for Streamlit
# EXPOSE 8501
#
# # Command to run the Streamlit app
# CMD ["streamlit", "run", "FinalApp_API.py", "--server.port=8501", "--server.address=0.0.0.0"]


# Use the official Python 3.10 image as the base
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt to the container
COPY ./requirements.txt /app/requirements.txt

# Upgrade pip and install dependencies from requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the entire app into the working directory
COPY ./app /app

# Expose port 8501 for Streamlit
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "FinalApp_API.py", "--server.port=8501", "--server.address=0.0.0.0"]