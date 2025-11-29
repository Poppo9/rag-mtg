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
    # Get the existing collection
    chroma_collection = chroma_client.get_collection("pdf_collection")
    # Wrap the collection in LlamaIndex's vector store adapter
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    # Create storage context pointing to the existing vector store
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    # Initialize the same embedding model used when creating the index
    embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    # Load the index from the existing vector store
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model)
    # Query the index
    query_engine = index.as_query_engine(similarity_top_k=5)
    response = query_engine.query(question)
    
    # print(f"Response type: {type(response)}")
    # print(f"Has source_nodes: {hasattr(response, 'source_nodes')}")
    
    # if hasattr(response, 'source_nodes'):
    #     print(f"Number of source nodes: {len(response.source_nodes)}")
    #     print("\n--- TOP 5 DOCUMENTS FOUND ---")
    #     for i, node in enumerate(response.source_nodes, 1):
    #         print(f"\n[Document {i}]")
    #         print(f"Score: {node.score if hasattr(node, 'score') else 'N/A'}")
    #         print(f"Text preview: {node.text[:200]}...")
    #         print(f"Full text length: {len(node.text)} characters")
    # else:
    #     print("WARNING: No source_nodes attribute found!")
    
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