# backend/services/answer_generator.py
"""根据查询结果生成自然语言回答"""

from services.llm_service import call_llm
import json

ANSWER_PROMPT = """
你是一个宝可梦知识图谱问答助手。根据用户的提问和图数据库查询结果，生成自然语言回答。

## 用户提问
{question}
## 查询结果
{results}

请用简洁友好的中文回答。如果查询结果为空，请告知未找到相关信息。
""".strip()


def generate_answer(question: str, results: list) -> str:
    """根据查询结果生成自然语言回答

    Args:
        question: 用户问题
        results: Neo4j 查询结果（列表格式）

    Returns:
        自然语言回答
    """
    results_text = json.dumps(results, ensure_ascii=False, indent=2) if results else "[]（无结果）"
    prompt = ANSWER_PROMPT.format(question=question, results=results_text)
    return call_llm(prompt, temperature=0.3)
