from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from app_v2.config import settings
from functools import lru_cache


@lru_cache(maxsize=1)
def get_embeddings_model():
    return OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=settings.OPENAI_API_KEY
)

@lru_cache(maxsize=1)
def get_llm_chat():
    return ChatOpenAI(
        model_name="gpt-4.5-preview",
        temperature=0,
        openai_api_key=settings.OPENAI_API_KEY
    )