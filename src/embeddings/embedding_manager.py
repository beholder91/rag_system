# src/embeddings/embedding_manager.py

from typing import List
import torch
from transformers import AutoModel, AutoTokenizer

class EmbeddingManager:
    """管理文本嵌入的计算和存储"""
    
    def __init__(self, model_name: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)
        self.model.eval()

    def compute_embeddings(self, texts: List[str], batch_size: int = 32) -> torch.Tensor:
        """计算文本的嵌入向量"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_texts = [f"为这段文字生成表示：{text}" for text in batch_texts]
            
            encoded = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            )
            
            input_ids = encoded['input_ids'].to(self.device)
            attention_mask = encoded['attention_mask'].to(self.device)
            
            with torch.no_grad():
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
                batch_embeddings = outputs.last_hidden_state[:, 0]
                embeddings.append(batch_embeddings)
        
        all_embeddings = torch.cat(embeddings, dim=0)
        return torch.nn.functional.normalize(all_embeddings, p=2, dim=1)

    def compute_similarity(self, query_embedding: torch.Tensor, doc_embeddings: torch.Tensor) -> torch.Tensor:
        """计算查询向量与文档向量之间的相似度"""
        return torch.cosine_similarity(query_embedding, doc_embeddings)