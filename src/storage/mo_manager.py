# src/storage/mo_manager.py

import pymysql
from typing import List, Dict, Optional
import numpy as np
from config.config import (
    MO_HOST, MO_PORT, MO_USER, MO_PASSWORD, 
    MO_DATABASE, MO_TABLE, VECTOR_DIMENSION
)

class MOManager:
    """MatrixOne database manager for vector storage and retrieval"""
    
    def __init__(self):
        """Initialize database connection and setup"""
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
        """Initialize database and table if they don't exist"""
        try:
            # Create database if not exists
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MO_DATABASE}")
            self.cursor.execute(f"USE {MO_DATABASE}")
            
            # Create table if not exists
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
            
            # Create vector index for better performance
            try:
                self.cursor.execute("SET GLOBAL experimental_ivf_index = 1")
                # Check if index exists
                self.cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.statistics 
                    WHERE table_schema = '{MO_DATABASE}' 
                    AND table_name = '{MO_TABLE}' 
                    AND index_name = 'idx_embedding'
                """)
                if self.cursor.fetchone()[0] == 0:
                    index_sql = f"""
                    CREATE INDEX idx_embedding 
                    USING IVFFLAT ON {MO_TABLE}(embedding) 
                    LISTS=1 OP_TYPE vector_l2_ops
                    """
                    self.cursor.execute(index_sql)
            except Exception as e:
                print(f"Warning: Vector index creation failed: {e}")
            
        except Exception as e:
            raise Exception(f"Failed to initialize database: {e}")

    def store_document(self, file_path: str, chunk_content: str, embedding: List[float]) -> bool:
        """Store document chunk and its embedding"""
        try:
            # Check if this chunk already exists
            check_sql = f"""
            SELECT id FROM {MO_TABLE} 
            WHERE file_path = %s AND chunk_content = %s
            """
            self.cursor.execute(check_sql, (file_path, chunk_content))
            if self.cursor.fetchone():
                return False  # Skip if already exists
            
            # Insert new document
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
        """Retrieve similar documents using vector similarity search"""
        try:
            # Convert l2_distance to similarity score (0-1 range)
            query_sql = f"""
            SELECT 
                file_path, 
                chunk_content, 
                1/(1 + l2_distance(embedding, %s)) as similarity 
            FROM {MO_TABLE} 
            ORDER BY similarity DESC 
            LIMIT {top_k}
            """
            self.cursor.execute(query_sql, (str(query_embedding),))
            results = []
            for file_path, content, score in self.cursor.fetchall():
                results.append({
                    'text': content,
                    'metadata': {'source': file_path},
                    'score': float(score)
                })
            return results
            
        except Exception as e:
            print(f"Failed to retrieve similar documents: {e}")
            return []

    def close(self):
        """Close database connection safely"""
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
        """Safe destructor"""
        try:
            self.close()
        except:
            pass  # Suppress any errors during cleanup

    def batch_store_documents(self, documents: List[Dict]) -> List[bool]:
        """Batch store multiple documents
        
        Args:
            documents: List of dicts with keys 'file_path', 'chunk_content', 'embedding'
        
        Returns:
            List of booleans indicating success/failure for each document
        """
        results = []
        for doc in documents:
            result = self.store_document(
                doc['file_path'],
                doc['chunk_content'],
                doc['embedding']
            )
            results.append(result)
        return results