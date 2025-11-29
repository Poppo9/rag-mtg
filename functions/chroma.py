import os
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

def query_chroma_index(question: str) -> str:
    # Reconnect to the existing persistent Chroma database
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    # Get the existing collection (use get_collection, not get_or_create_collection)
    chroma_collection = chroma_client.get_collection("pdf_collection")
    # Wrap the collection in LlamaIndex's vector store adapter
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    # Create storage context pointing to the existing vector store
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    # Initialize the same embedding model used when creating the index
    embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    # Load the index from the existing vector store
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model)
    # Now you can query the index
    query_engine = index.as_query_engine()
    response = query_engine.query(question)
    return response