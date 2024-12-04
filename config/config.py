# config/config.py

from pathlib import Path
from config.api_key import API_KEY

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_BASE_DIR = DATA_DIR / "new_knowledge_base"

# Model configurations
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BATCH_SIZE = 32

# API configurations 
API_URL = "https://neolink-ai.com/model/api/v1/chat/completions"

# LLM configurations
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MODEL = "Qwen/Qwen2-7B-Instruct"

# MatrixOne configurations
MO_HOST = "localhost"
MO_PORT = 6001
MO_USER = "root" 
MO_PASSWORD = "111"
MO_DATABASE = "rag_db"
MO_TABLE = "document_store"
VECTOR_DIMENSION = 1024  # 根据embedding模型输出维度设置