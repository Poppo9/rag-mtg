import os
import chromadb

from dotenv import load_dotenv

from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)

from llama_index.embeddings.nvidia import NVIDIAEmbedding
from llama_index.llms.nvidia import NVIDIA
from llama_index.vector_stores.chroma import ChromaVectorStore

from functions.rule_downloader import download_rules


# Load environment variables from .env file
load_dotenv(override=True)
NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]

def query_chroma_index(question: str) -> str:
    # Reconnect to the existing persistent Chroma database
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    # Get the existing collection
    chroma_collection = chroma_client.get_collection("documents_collection")
    # Wrap the collection in LlamaIndex's vector store adapter
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    # Create storage context pointing to the existing vector store
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    # Initialize the same embedding model used when creating the index
    # LLM to generate answers based on retrieved information
    Settings.llm = NVIDIA(model="meta/llama-3.1-8b-instruct", api_key=os.getenv("NVIDIA_API_KEY"))
    # Embedding model to convert text into vectors for retrieval
    embed_model = NVIDIAEmbedding(model="nvidia/nv-embed-v1", api_key=os.getenv("NVIDIA_API_KEY"))
    # Load the index from the existing vector store
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model)
    # Query the index
    query_engine = index.as_query_engine(similarity_top_k=5)
    response = query_engine.query(question)
    
    # Format the output
    output_parts = []
    
    if hasattr(response, 'source_nodes') and response.source_nodes:
        output_parts.append("=== RETRIEVED DOCUMENTS ===\n")
        for i, node in enumerate(response.source_nodes, 1):
            output_parts.append(f"[Document {i}]")
            output_parts.append(node.text)
            output_parts.append("")
    else:
        output_parts.append("No relevant documents found.")
    
    result = "\n".join(output_parts)
    print(f"Final output length: {len(result)} characters\n")
    return result


def setup_chroma_index(
    documents_dir: str = "documents",
    chroma_path: str = "./chroma_db",
    collection_name: str = "documents_collection",
):
    """
    Download/update documents, create/open a persistent Chroma collection,
    build a LlamaIndex VectorStoreIndex, and return all relevant objects.

    Returns:
        {
            "index": VectorStoreIndex,
            "chroma_client": PersistentClient,
            "collection": Collection,
            "vector_store": ChromaVectorStore,
            "storage_context": StorageContext,
            "documents": list[Document],
        }
    """

    # Load environment variables
    load_dotenv()

    nvidia_api_key = os.environ["NVIDIA_API_KEY"]

    # Download latest rules
    if download_rules():
        print("Regole scaricate con successo.")

    # Load documents
    documents = SimpleDirectoryReader(
        input_dir=documents_dir
    ).load_data()

    # Open/create persistent Chroma database
    chroma_client = chromadb.PersistentClient(
        path=chroma_path
    )

    # Open/create collection
    chroma_collection = chroma_client.get_or_create_collection(
        collection_name
    )

    # Create vector store
    vector_store = ChromaVectorStore(
        chroma_collection=chroma_collection
    )

    # Create storage context
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )

    # Embedding model
    embed_model = NVIDIAEmbedding(
        model="nvidia/nv-embed-v1",
        api_key=nvidia_api_key,
    )

    # Build index
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
    )

    return {
        "index": index,
        "chroma_client": chroma_client,
        "collection": chroma_collection,
        "vector_store": vector_store,
        "storage_context": storage_context,
        "documents": documents,
    }    