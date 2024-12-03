# src/rag/rag_system.py

from typing import Dict, List, Optional
from pathlib import Path
import numpy as np

from src.processors.document_processor import DocumentProcessor
from src.embeddings.embedding_manager import EmbeddingManager
from src.llm.llm_client import LLMClient
from config.config import EMBEDDING_MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP

class RAGSystem:
    """检索增强生成系统"""
    
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
        
        self.documents = []
        self.embeddings = None
        
        self.load_knowledge_base(knowledge_base_dir)

    def load_knowledge_base(self, directory: str):
        """加载并处理知识库文档"""
        self.documents = self.doc_processor.process_documents(directory)
        
        if self.documents:
            texts = [doc.page_content for doc in self.documents]
            self.embeddings = self.embedding_manager.compute_embeddings(texts)
        else:
            print("警告：没有加载到任何文档")

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """检索相关文档"""
        if not self.documents or self.embeddings is None:
            return []
            
        query_embedding = self.embedding_manager.compute_embeddings([query])
        similarities = self.embedding_manager.compute_similarity(
            query_embedding,
            self.embeddings
        )[0]  # Get the first (and only) query's similarities
        
        # Get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'text': self.documents[idx].page_content,
                'metadata': self.documents[idx].metadata,
                'score': float(similarities[idx])
            })
        
        return results

    def answer_question(
        self,
        query: str,
        top_k: int = 5,
        max_tokens: int = 1000
    ) -> Dict:
        """完整的问答流程"""
        retrieved_docs = self.retrieve(query, top_k=top_k)
        prompt = self.llm_client.format_prompt(query, retrieved_docs)
        answer = self.llm_client.generate_response(prompt, max_tokens=max_tokens)
        
        return {
            'query': query,
            'answer': answer,
            'retrieved_documents': retrieved_docs,
            'prompt': prompt
        }