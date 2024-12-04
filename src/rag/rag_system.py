# src/rag/rag_system.py

from typing import Dict, List, Optional
from pathlib import Path

from src.processors.document_processor import DocumentProcessor
from src.embeddings.embedding_manager import EmbeddingManager
from src.llm.llm_client import LLMClient
from src.storage.mo_manager import MOManager
from src.storage.base_storage import BaseStorage, MemoryStorage
from config.config import EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP

class RAGSystem:
    """检索增强生成系统 - 支持存储降级"""
    
    def __init__(
        self,
        knowledge_base_dir: str,
        api_key: str,
        embedding_model_name: str = EMBEDDING_MODEL_NAME,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP
    ):
        self.doc_processor = DocumentProcessor(chunk_size, chunk_overlap)
        self.embedding_manager = EmbeddingManager(embedding_model_name)
        self.llm_client = LLMClient(api_key)
        
        # Try to initialize MatrixOne storage, fallback to memory storage if failed
        try:
            self.storage = MOManager()
            print("INFO: Using MatrixOne for vector storage")
        except Exception as e:
            print(f"WARNING: Failed to initialize MatrixOne storage, falling back to memory storage: {e}")
            self.storage = MemoryStorage()
        
        if knowledge_base_dir:
            self.load_knowledge_base(knowledge_base_dir)

    def load_knowledge_base(self, directory: str):
        documents = self.doc_processor.process_documents(directory)
        
        if documents:
            print(f"Processing {len(documents)} document chunks...")
            for doc in documents:
                embedding = self.embedding_manager.compute_embeddings([doc.page_content])[0]
                
                stored = self.storage.store_document(
                    file_path=doc.metadata['source'],
                    chunk_content=doc.page_content,
                    embedding=embedding.tolist()
                )
                if stored:
                    print(f"Stored new document chunk from: {doc.metadata['source']}")
        else:
            print("Warning: No documents loaded")

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        query_embedding = self.embedding_manager.compute_embeddings([query])[0]
        return self.storage.retrieve_similar(query_embedding.tolist(), top_k)

    def answer_question(
        self,
        query: str,
        top_k: int = 5,
        max_tokens: int = 1000
    ) -> Dict:
        retrieved_docs = self.retrieve(query, top_k=top_k)
        prompt = self.llm_client.format_prompt(query, retrieved_docs)
        answer = self.llm_client.generate_response(prompt, max_tokens=max_tokens)
        
        return {
            'query': query,
            'answer': answer,
            'retrieved_documents': retrieved_docs,
            'prompt': prompt
        }

    def __del__(self):
        """确保正确关闭数据库连接"""
        if hasattr(self, 'storage') and isinstance(self.storage, MOManager):
            self.storage.close()