import logging
import requests
from typing import Optional, List, Dict
from pathlib import Path

class ParseClient:
    """Parse Server客户端"""
    
    def __init__(self, server_url: str, timeout: int = 180):
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        
        # 配置日志
        logging.getLogger('pdfminer').setLevel(logging.WARNING)
        logging.getLogger('PIL').setLevel(logging.WARNING)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
    def parse_document(self, file_path: str) -> List[Dict]:
        """使用Parse Server解析文档，返回文档块列表"""
        self.logger.info(f"开始处理文件: {Path(file_path).name}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                
                response = requests.post(
                    f"{self.server_url}/parse/all_doc",
                    files=files,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                result = response.json()
                
                if not isinstance(result, dict) or 'blocks' not in result:
                    self.logger.error("响应中缺少blocks字段")
                    return []
                
                # 处理并返回有效的文档块
                blocks = []
                for block in result['blocks']:
                    if not block.get('is_image') and block.get('content'):
                        blocks.append({
                            'content': block['content'],
                            'metadata': {
                                'source': file_path,
                                'block_type': block.get('type', 'text'),
                                'page_num': block.get('page_num'),
                                'position': block.get('position'),
                                'is_title': block.get('is_title', False),
                                'confidence': block.get('confidence', 1.0)
                            }
                        })
                
                self.logger.info(f"Parse Server解析成功，获取到 {len(blocks)} 个文本块")
                return blocks
                
        except requests.Timeout:
            self.logger.error("Parse Server请求超时")
            raise
        except requests.RequestException as e:
            self.logger.error(f"Parse Server请求失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"解析过程出错: {e}")
            raise
            
    def check_health(self) -> bool:
        """检查Parse Server是否可用"""
        try:
            response = requests.get(f"{self.server_url}/docs", timeout=5)
            return response.status_code == 200
        except:
            return False