# src/storage/mo_manager.py

import pymysql
from typing import List, Dict, Optional
import numpy as np
from config.config import (
    MO_HOST, MO_PORT, MO_USER, MO_PASSWORD, 
    MO_DATABASE, MO_TABLE, VECTOR_DIMENSION
)
from .base_storage import BaseStorage

class MOManager(BaseStorage):
    """MatrixOne database manager for vector storage"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.is_connected = False
        self.connect()
        self.init_database()

    def connect(self):
        """Connect to MatrixOne database"""
        if not self.is_connected:
            try:
                self.conn = pymysql.connect(
                    host=MO_HOST,
                    port=MO_PORT,
                    user=MO_USER,
                    password=MO_PASSWORD,
                    autocommit=True
                )
                self.cursor = self.conn.cursor()
                self.is_connected = True
            except Exception as e:
                raise Exception(f"Failed to connect to MatrixOne: {e}")

    def init_database(self):
        """Initialize database and table"""
        try:
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MO_DATABASE}")
            self.cursor.execute(f"USE {MO_DATABASE}")
            
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {MO_TABLE} (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                file_path VARCHAR(512),
                chunk_content TEXT,
                embedding VECF32({VECTOR_DIMENSION}),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.cursor.execute(create_table_sql)
            
            # Simplified index creation
            try:
                self.cursor.execute("SET GLOBAL experimental_ivf_index = 1")
                index_sql = f"""
                CREATE INDEX idx_embedding 
                ON {MO_TABLE}(embedding)
                """
                self.cursor.execute(index_sql)
            except Exception as e:
                print(f"Warning: Vector index creation failed: {e}")
            
        except Exception as e:
            raise Exception(f"Failed to initialize database: {e}")

    def store_document(self, file_path: str, chunk_content: str, embedding: List[float]) -> bool:
        try:
            check_sql = f"""
            SELECT id FROM {MO_TABLE} 
            WHERE file_path = %s AND chunk_content = %s
            """
            self.cursor.execute(check_sql, (file_path, chunk_content))
            if self.cursor.fetchone():
                return False
            
            insert_sql = f"""
            INSERT INTO {MO_TABLE} (file_path, chunk_content, embedding) 
            VALUES (%s, %s, %s)
            """
            self.cursor.execute(insert_sql, (file_path, chunk_content, str(embedding)))
            return True
        except Exception as e:
            print(f"Failed to store document: {e}")
            return False

    def retrieve_similar(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """Retrieve similar documents using cosine similarity"""
        try:
            # 首先获取所有必要的数据
            query_sql = f"""
            SELECT 
                file_path, 
                chunk_content,
                embedding  
            FROM {MO_TABLE}
            """
            self.cursor.execute(query_sql)
            
            # 计算余弦相似度并排序
            results = []
            query_embedding = np.array(query_embedding)
            query_norm = np.linalg.norm(query_embedding)
            
            for file_path, content, embedding_str in self.cursor.fetchall():
                # 将字符串形式的embedding转换回向量
                doc_embedding = np.array(eval(embedding_str))
                doc_norm = np.linalg.norm(doc_embedding)
                
                if query_norm == 0 or doc_norm == 0:
                    similarity = 0
                else:
                    similarity = np.dot(query_embedding, doc_embedding) / (query_norm * doc_norm)
                
                results.append({
                    'text': content,
                    'metadata': {'source': file_path},
                    'score': float(similarity)
                })
            
            # 按相似度排序并返回top_k个结果
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"Failed to retrieve similar documents: {e}")
            return []

    def close(self):
        try:
            if self.is_connected:
                if self.cursor:
                    self.cursor.close()
                    self.cursor = None
                if self.conn:
                    self.conn.close()
                    self.conn = None
                self.is_connected = False
        except Exception as e:
            print(f"Warning: Error while closing database connection: {e}")

    def __del__(self):
        try:
            self.close()
        except:
            pass

    def delete_document(self, file_path: str) -> bool:
        """Delete all chunks and embeddings for a given file from MatrixOne"""
        try:
            delete_sql = f"""
            DELETE FROM {MO_TABLE} 
            WHERE file_path = %s
            """
            self.cursor.execute(delete_sql, (file_path,))
            return True
        except Exception as e:
            print(f"Failed to delete document from MatrixOne: {e}")
            return False