import json
import faiss
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from typing import List, Optional
import logging

# Suppress TensorFlow warnings (if still present)
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentRetriever:
    def __init__(self, faiss_index_path: str, docstore_path: str, embedding_model_name: str = "BAAI/bge-m3"):
        """
        Initialize the retriever with FAISS index, docstore, and embedding model.
        
        Args:
            faiss_index_path (str): Path to the saved FAISS index file.
            docstore_path (str): Path to the saved docstore JSON file.
            embedding_model_name (str): Name of the embedding model (default: BAAI/bge-m3).
        """
        try:
            # Load the embedding model
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=embedding_model_name,
                model_kwargs={"device": "cpu"}
            )
            
            # Load the docstore and index-to-docstore mapping
            with open(docstore_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                docstore_data = data["docstore"]
                index_to_docstore_id = data["index_to_docstore_id"]
            
            # Convert index_to_docstore_id keys to integers
            index_to_docstore_id = {int(k) if k.isdigit() else k: v for k, v in index_to_docstore_id.items()}
            
            # Reconstruct the docstore
            self.docstore = InMemoryDocstore({
                k: Document(page_content=v["page_content"], metadata=v["metadata"])
                for k, v in docstore_data.items()
            })
            
            # Load the FAISS index
            faiss_index = faiss.read_index(faiss_index_path)
            
            # Validate FAISS index size
            logger.info(f"FAISS index contains {faiss_index.ntotal} vectors")
            logger.info(f"Docstore contains {len(docstore_data)} documents")
            if faiss_index.ntotal != len(index_to_docstore_id):
                logger.warning(
                    f"FAISS index size ({faiss_index.ntotal}) does not match index_to_docstore_id size ({len(index_to_docstore_id)})."
                )
            
            # Create the LangChain FAISS vector store
            self.vectorstore = FAISS(
                embedding_function=self.embedding_model,
                index=faiss_index,
                docstore=self.docstore,
                index_to_docstore_id=index_to_docstore_id
            )
            
            # Set a default relevance threshold (lowered for debugging)
            self.relevance_threshold = 0.5  # Lowered from 0.75 to capture more documents
            
            logger.info("Retriever initialized successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize retriever: {str(e)}")
            raise
    
    def retrieve(self, query: str, top_k: int = 3, relevance_threshold: Optional[float] = None) -> List[Document]:
        """
        Retrieve relevant documents for a given query.
        
        Args:
            query (str): The input query.
            top_k (int): Maximum number of documents to return (default: 3).
            relevance_threshold (float, optional): Minimum similarity score for relevance.
                                                 If None, uses default threshold.
        
        Returns:
            List[Document]: List of relevant documents, or empty list if none meet the threshold.
        """
        try:
            # Use provided threshold or default
            threshold = relevance_threshold if relevance_threshold is not None else self.relevance_threshold
            
            # Perform similarity search with scores
            results = self.vectorstore.similarity_search_with_score(query, k=top_k)
            
            # Log all results for debugging
            logger.info(f"Raw similarity search results for query: {query}")
            relevant_docs = []
            for i, (doc, score) in enumerate(results, 1):
                similarity = 1 - (score ** 2) / 2
                logger.info(
                    f"Result {i}: Similarity = {similarity:.3f}, Threshold = {threshold}, "
                    f"Content = {doc.page_content[:100]}..."
                )
                if similarity >= threshold:
                    relevant_docs.append(doc)
                else:
                    logger.debug(f"Document discarded (similarity {similarity:.3f} < threshold {threshold})")
            
            logger.info(f"Retrieved {len(relevant_docs)} relevant documents for query: {query}")
            return relevant_docs
            
        except Exception as e:
            logger.error(f"Error during retrieval: {str(e)}")
            return []
    
    def set_relevance_threshold(self, threshold: float):
        """
        Update the relevance threshold.
        
        Args:
            threshold (float): New relevance threshold (0 to 1).
        """
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        self.relevance_threshold = threshold
        logger.info(f"Relevance threshold updated to {threshold}")

# Example usage
if __name__ == "__main__":
    try:
        # Initialize the retriever
        retriever = IntelligentRetriever(
            faiss_index_path="faiss_index.bin",
            docstore_path="docstore.json",
            embedding_model_name="BAAI/bge-m3"
        )
        
        # Test query
        test_queries = [
            "What are the fishing restrictions around Îles Zembra?",
            "Random query about cooking pasta"
        ]
        for query in test_queries:
            print(f"\nQuery: {query}")
            results = retriever.retrieve(query, top_k=3)
            if results:
                print("Relevant Documents:")
                for i, doc in enumerate(results, 1):
                    print(f"{i}. {doc.page_content}")
                    print(f"   Metadata: {doc.metadata}")
            else:
                print("No relevant documents found.")
                
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")