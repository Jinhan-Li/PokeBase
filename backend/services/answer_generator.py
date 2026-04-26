# backend/services/answer_generator.py
"""根据查询结果生成自然语言回答"""

import logging
import json

from services.llm_service import call_llm

logger = logging.getLogger(__name__)

ANSWER_PROMPT = """
你是一个宝可梦知识图谱问答助手。根据用户的提问和图数据库查询结果，生成自然语言回答。

## 用户提问
{question}
## 执行的 Cypher 查询
{cypher}
## 查询结果
{results}

请用简洁友好的中文回答用户的问题。如果查询结果为空，请告知用户未找到相关信息，并建议用户尝试用英文精灵名称提问。
""".strip()


def generate_answer(question: str, cypher: str, results: list) -> str:
    """根据查询结果生成自然语言回答

    Args:
        question: 用户问题
        cypher: 执行的 Cypher 查询语句
        results: Neo4j 查询结果（列表格式）

    Returns:
        自然语言回答
    """
    results_text = json.dumps(results, ensure_ascii=False, indent=2) if results else "[]（无结果）"
    prompt = ANSWER_PROMPT.format(
        question=question,
        cypher=cypher,
        results=results_text
    )

    try:
        answer = call_llm(prompt, temperature=0.3)
        return answer
    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        # 降级回答：直接返回查询结果的中文描述
        if not results:
            return f"未找到与「{question}」相关的信息，请尝试用英文精灵名称提问。"
        return f"查询结果：{json.dumps(results, ensure_ascii=False)[:200]}"
