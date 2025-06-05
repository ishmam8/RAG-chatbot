from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app_v2.api import auth as auth_router
from app_v2.api import chat as chat_router
from app_v2.api import documents as docs_router
from app_v2.database import init_db

app = FastAPI(
    title="RAG Chatbot Backend with JWT Auth",
    description="FastAPI service powering a RAG-based chatbot. Uses JWT for authentication.",
    version="1.0.0",
)

# ----------- CORS (allow your frontend or React Native) -----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; in prod, replace "*" with your frontend domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- Include Routers -----------
app.include_router(auth_router.router, prefix="/auth")
# app.include_router(chat_router.router, prefix="/chat")
app.include_router(docs_router.router, prefix="/documents")


# ----------- Startup Event: initialize the database & any heavy models -----------
@app.on_event("startup")
async def startup_event():
    # Create DB tables
    init_db()

    # (If you have heavy models to load, you can do it here, e.g. embeddings or LLM clients.)
    # from app.core.embeddings import initialize_model
    # from app.core.vector_store import initialize_vectorstore
    # await initialize_model()
    # await initialize_vectorstore()
    pass

@app.get("/")
async def read_root():
    return {"message": "API is running"}