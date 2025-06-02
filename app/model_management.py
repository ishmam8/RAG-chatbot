
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.llms import CTransformers
import openai
from io import StringIO

# # Create embeddings using Sentence Transformers
# embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})


# # Initialize OpenAIEmbeddings
embeddings_model_large = OpenAIEmbeddings(
    model='text-embedding-3-large',  # You can choose other models if available
    # openai_api_key=os.getenv("OPENAI_API_KEY")  # Fetches the API key from environment variables
    openai_api_key=OPENAI_API_KEY# Fetches the API key from environment variables

)


# embeddings_model = OpenAIEmbeddings(
# #     model='text-embedding-3-large',  # You can choose other models if available
#     model='text-embedding-ada-002',  # You can choose other models if available
#     # openai_api_key=os.getenv("OPENAI_API_KEY")  # Fetches the API key from environment variables
#     # openai_api_key=""# Fetches the API key from environment variables
#     openai_api_key=OPENAI_API_KEY
#
# )


# # Set your OpenAI API key
# openai.api_key = 'your-openai-api-key'
# def get_embedding(text, model="text-embedding-ada-002"):
#     response = openai.Embedding.create(
#         input=text,
#         model=model
#     )
#     embedding = response['data'][0]['embedding']
#     return embedding


llm_chat = ChatOpenAI(model_name="gpt-4.5-preview", temperature=0,
                 api_key=OPENAI_API_KEY
                 )

# Load the model of choice
def load_llm():
    llm = CTransformers(
        model="llama-2-7b-chat.ggmlv3.q8_0.bin",
        model_type="llama",
        max_new_tokens=512,
        temperature=0.5
    )
    return llm