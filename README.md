# Build_Agent

# RAG-CHATBOT

A **Retrieval-Augmented Generation chatbot** using LangChain, OpenAI GPT-4.5, and FAISS for semantic search. Runs as an API on an AWS Ubuntu server, managed by Supervisor.

---

## What does this project do?

- Lets you **chat with an LLM (GPT-4.5)** that can look up information from your own documents.
- Uses **FAISS** to search your documents and find relevant content for answers.
- Built using **LangChain** for easy chaining of LLM and retrieval steps.
- API endpoints are ready for integration with any web or mobile frontend.

---

## Main Technologies

- **Python 3.9+**
- **FastAPI ASGI (Uvicorn)**: Runs the API server
- **LangChain**: Handles RAG logic
- **OpenAI GPT-4.5**: Large Language Model
- **FAISS**: Fast vector search
- **Supervisor**: Keeps the server running on AWS Ubuntu

---

## Folder Structure

- `app_v2/` — Main backend code
    - `api/` — API endpoints (e.g. chat, auth)
    - `core/` — Core logic (authentication, model management)
    - `utils/` — Utility functions (embedding, database, retrieval)
    - Other files — App configuration, models, schemas
- `.gitignore` — Files/folders not tracked by git
- `Dockerfile` — For Docker deployments
- `requirements.txt` — Python dependencies
- `supervisor-staging.conf` — Supervisor config for deployment

---

## Getting Started

```sh
1. Clone the repo
git clone https://github.com/yourusername/rag-chatbot.git
cd rag-chatbot

2. Install dependencies
pip install -r requirements.txt

3. Add your environment variables
Create a .env file (or set in shell) with your OpenAI API key:
OPENAI_API_KEY=sk-xxxxxxx

4. Start the API locally
uvicorn app_v2.main:app --reload
Your API will be running at http://localhost:8000
Deployment on AWS Ubuntu (using Supervisor)

Install Python and Supervisor:
sudo apt update
sudo apt install python3-pip supervisor
pip3 install -r requirements.txt

Set up Supervisor:
Edit supervisor-staging.conf (sample below):
[program:rag-chatbot]
directory=/home/ubuntu/rag-chatbot/app_v2
command=uvicorn main:app --host 0.0.0.0 --port 8000
autostart=true
autorestart=true
stderr_logfile=/var/log/rag-chatbot.err.log
stdout_logfile=/var/log/rag-chatbot.out.log

Then copy and enable it:

sudo cp supervisor-staging.conf /etc/supervisor/conf.d/rag-chatbot.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start rag-chatbot

API Endpoints (examples)
POST /api/chat — Send a message, get a response
POST /api/auth — Login/authenticate (if implemented)
POST /api/documents — Upload or manage documents
