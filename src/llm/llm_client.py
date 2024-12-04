# src/llm/llm_client.py

from typing import Optional, Dict, Any, List
import requests
from datetime import datetime
import pytz
from config.config import API_URL, DEFAULT_MODEL, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE

class LLMClient:
    """LLM API客户端"""
    
    def __init__(self, api_key: str):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": api_key
        }

    def generate_response(
        self,
        prompt: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        model: str = DEFAULT_MODEL
    ) -> Optional[str]:
        """调用LLM API生成回答"""
        try:
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(API_URL, headers=self.headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return None

    def get_beijing_time(self) -> str:
        """获取北京时间"""
        beijing_tz = pytz.timezone('Asia/Shanghai')
        beijing_time = datetime.now(beijing_tz)
        weekday_map = {
            0: '一',
            1: '二',
            2: '三',
            3: '四',
            4: '五',
            5: '六',
            6: '日'
        }
        weekday = weekday_map[beijing_time.weekday()]
        return f"{beijing_time.strftime('%Y年%m月%d日 %H:%M:%S')} 星期{weekday}"

    def format_prompt(self, query: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """格式化提示模板"""
        current_time = self.get_beijing_time()
        
        prompt = f"""你是一个专业的网络运维工程师助手。请基于以下信息回答问题。如果文档中的信息不足以完整回答问题，请明确指出。

当前北京时间：{current_time}

回答要求：
1. 保持专业性和准确性
2. 如果需要引用文档内容，请明确指出信息来源
3. 如果问题涉及多个方面，请分点回答
4. 回答要简洁明了，避免冗余
5. 如果问题涉及时间，请使用上述北京时间进行回答

问题：{query}

相关文档：
"""
        for idx, doc in enumerate(retrieved_docs, 1):
            prompt += f"\n文档{idx}:\n{doc['text']}\n"
            prompt += f"来源：{doc['metadata']['source']}\n"
            
        prompt += "\n请参考以上信息，结合自己的知识回答问题："
        return prompt