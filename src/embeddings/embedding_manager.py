# src/embeddings/embedding_manager.py

from typing import List, Dict, Any
import numpy as np
import requests
from config.config import API_KEY

class EmbeddingManager:
    """管理文本嵌入的计算和存储，使用NeoLink AI API"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.api_url = "https://neolink-ai.com/model/api/v1/embeddings"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

    def _call_api(self, text: str) -> List[float]:
        """调用NeoLink AI API获取嵌入向量"""
        try:
            payload = {
                "model": self.model_name,
                "input": text,
                "encoding_format": "float"
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return result['data'][0]['embedding']
            
        except Exception as e:
            print(f"获取嵌入向量失败: {e}")
            return None

    def compute_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """计算文本的嵌入向量"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # 由于API一次只处理一个文本，需要循环处理
            for text in batch_texts:
                embedding = self._call_api(text)
                if embedding:
                    embeddings.append(embedding)
        
        if not embeddings:
            raise Exception("未能获取任何嵌入向量")
            
        # 将所有嵌入向量转换为numpy数组
        embeddings_array = np.array(embeddings)
        
        # 进行L2归一化
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        normalized_embeddings = embeddings_array / norms
        
        return normalized_embeddings

    def compute_similarity(self, query_embedding: np.ndarray, doc_embeddings: np.ndarray) -> np.ndarray:
        """计算查询向量与文档向量之间的余弦相似度"""
        return np.dot(query_embedding, doc_embeddings.T)