from config.config import API_KEY, KNOWLEDGE_BASE_DIR
from src.rag.rag_system import RAGSystem

def main():
    # 初始化RAG系统
    rag = RAGSystem(
        knowledge_base_dir=KNOWLEDGE_BASE_DIR,
        api_key=API_KEY
    )
    
    # 测试问答
    question = "今天谁值班？"
    result = rag.answer_question(question)
    
    # 打印结果
    print(f"\n问题: {result['query']}")
    print(f"\n回答: {result['answer']}")
    # print("\n", "-" * 50, "prompt", "-" * 50)
    # print(result["prompt"])
    print("\n检索到的文档:")
    for idx, doc in enumerate(result['retrieved_documents'], 1):
        print(f"\n文档{idx}:")
        print(f"内容: {doc['text']}")
        print(f"来源: {doc['metadata']['source']}")
        print(f"相似度: {doc['score']:.3f}")

if __name__ == "__main__":
    main()