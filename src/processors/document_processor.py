from pathlib import Path
from typing import List, Optional
import logging
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .parse_client import ParseClient
from config.config import PARSE_SERVER_URL, PARSE_SERVER_TIMEOUT

class DocumentProcessor:
    """处理文档并提取文本内容的处理器"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.logger = logging.getLogger(__name__)
        # 初始化Parse Client
        self.parse_client = ParseClient(
            server_url=PARSE_SERVER_URL,
            timeout=PARSE_SERVER_TIMEOUT
        )
        
        # 文本分割器保持不变
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
            
        return " ".join(text.split())

    def load_document(self, file_path: str) -> Optional[str]:
        """加载并解析文档"""
        try:
            content = self.parse_client.parse_document(file_path)
            if content:
                return self.clean_text(content)
            return None
            
        except Exception as e:
            self.logger.error(f"处理文件 {file_path} 时出错: {e}")
            return None

    def process_documents(self, directory: str) -> List[Document]:
        """处理目录中的所有文档并返回分块后的文档列表"""
        documents = []
        # 扩展支持的文件类型
        supported_extensions = {'.doc', '.docx', '.pdf', '.txt', '.html', '.epub', 
                              '.jpg', '.jpeg', '.png'}
        
        for file_path in Path(directory).glob('**/*'):
            if file_path.suffix.lower() in supported_extensions:
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