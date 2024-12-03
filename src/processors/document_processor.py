# src/processors/document_processor.py

import re
from pathlib import Path
from typing import List, Optional
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    Docx2txtLoader,
    UnstructuredWordDocumentLoader
)

class DocumentProcessor:
    """处理Word文档并提取文本内容的处理器"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.loader_mapping = {
            '.docx': Docx2txtLoader,
            '.doc': UnstructuredWordDocumentLoader
        }
        self.cleaners = [
            (re.compile(r'\s+'), ' '),
            (re.compile(r'[^\w\s\u4e00-\u9fff.,?!;:()\[\]{}"\']+'), ''),
            (re.compile(r'\s+'), ' ')
        ]
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )

    def clean_text(self, text: str) -> str:
        """清理文本中的无意义字符"""
        if not text or not text.strip():
            return ""
        
        text = text.strip()
        for pattern, replacement in self.cleaners:
            text = pattern.sub(replacement, text)
        return text.strip()

    def load_document(self, file_path: str) -> Optional[str]:
        """加载单个Word文档并提取文本"""
        ext = Path(file_path).suffix.lower()
        
        if ext not in self.loader_mapping:
            return None
            
        try:
            loader_class = self.loader_mapping[ext]
            loader = loader_class(file_path)
            documents = loader.load()
            
            content = "\n".join([doc.page_content for doc in documents])
            cleaned_content = self.clean_text(content)
            
            if len(cleaned_content) < 10:
                return None
                
            return cleaned_content
            
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
            return None

    def process_documents(self, directory: str) -> List[Document]:
        """处理目录中的所有文档并返回分块后的文档列表"""
        documents = []
        
        for file_path in Path(directory).glob('**/*'):
            if file_path.suffix.lower() in self.loader_mapping:
                content = self.load_document(str(file_path))
                if content:
                    chunks = self.text_splitter.split_text(content)
                    for chunk in chunks:
                        documents.append(
                            Document(
                                page_content=chunk,
                                metadata={
                                    "source": str(file_path),
                                    "chunk_size": len(chunk)
                                }
                            )
                        )
        
        return documents