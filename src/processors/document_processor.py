from pathlib import Path
from typing import List, Optional
import logging
from langchain.docstore.document import Document
from .parse_client import ParseClient
from config.config import PARSE_SERVER_URL, PARSE_SERVER_TIMEOUT

class DocumentProcessor:
    """处理文档并提取文本内容的处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 初始化Parse Client
        self.parse_client = ParseClient(
            server_url=PARSE_SERVER_URL,
            timeout=PARSE_SERVER_TIMEOUT
        )

    def clean_text(self, text: str) -> str:
        """清理文本中的无意义字符"""
        if not text or not text.strip():
            return ""
            
        return " ".join(text.split())

    def load_document(self, file_path: str) -> List[Document]:
        """加载并解析文档，返回文档块列表"""
        try:
            blocks = self.parse_client.parse_document(file_path)
            if not blocks:
                return []
            
            documents = []
            for block in blocks:
                clean_content = self.clean_text(block['content'])
                if clean_content:
                    documents.append(
                        Document(
                            page_content=clean_content,
                            metadata=block['metadata']
                        )
                    )
            return documents
            
        except Exception as e:
            self.logger.error(f"处理文件 {file_path} 时出错: {e}")
            return []

    def process_documents(self, directory: str) -> List[Document]:
        """处理目录中的所有文档并返回文档块列表"""
        documents = []
        # 扩展支持的文件类型
        supported_extensions = {'.doc', '.docx', '.pdf', '.txt', '.html', '.epub', 
                              '.jpg', '.jpeg', '.png'}
        
        for file_path in Path(directory).glob('**/*'):
            if file_path.suffix.lower() in supported_extensions:
                doc_blocks = self.load_document(str(file_path))
                if doc_blocks:
                    documents.extend(doc_blocks)
                    self.logger.info(f"成功处理文件 {file_path.name}，获取到 {len(doc_blocks)} 个文档块")
        
        return documents