# src/storage/base_storage.py

from abc import ABC, abstractmethod
from typing import List, Dict
import numpy as np

class BaseStorage(ABC):
    """Storage interface for vector database"""
    
    @abstractmethod
    def store_document(self, file_path: str, chunk_content: str, embedding: List[float]) -> bool:
        """Store a document chunk and its embedding"""
        pass
        
    @abstractmethod
    def retrieve_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """Retrieve similar documents"""
        pass

    @abstractmethod
    def delete_document(self, file_path: str) -> bool:
        """Delete all chunks and embeddings for a given file path"""
        pass

class MemoryStorage(BaseStorage):
    """In-memory storage implementation for fallback"""
    
    def __init__(self):
        self.documents = []
        print("INFO: Using in-memory storage as fallback")
        
    def store_document(self, file_path: str, chunk_content: str, embedding: List[float]) -> bool:
        # Check for duplicates
        for doc in self.documents:
            if doc['file_path'] == file_path and doc['content'] == chunk_content:
                return False
                
        self.documents.append({
            'file_path': file_path,
            'content': chunk_content,
            'embedding': embedding
        })
        return True
        
    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0
        return np.dot(a, b) / (norm_a * norm_b)
        
    def retrieve_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        if not self.documents:
            return []
            
        query_embedding = np.array(query_embedding)
        
        # Calculate cosine similarities
        similarities = []
        for doc in self.documents:
            doc_embedding = np.array(doc['embedding'])
            similarity = self.cosine_similarity(query_embedding, doc_embedding)
            similarities.append((similarity, doc))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top_k results
        results = []
        for similarity, doc in similarities[:top_k]:
            results.append({
                'text': doc['content'],
                'metadata': {'source': doc['file_path']},
                'score': float(similarity)
            })
        
        return results

    def delete_document(self, file_path: str) -> bool:
        """Delete all chunks related to the specified file"""
        try:
            # Filter out all documents from the specified file
            self.documents = [doc for doc in self.documents if doc['file_path'] != file_path]
            return True
        except Exception as e:
            print(f"Failed to delete document from memory storage: {e}")
            return False