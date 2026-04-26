# backend/services/cypher_generator.py
"""根据用户问题生成 Cypher 查询语句"""

import logging
import re

from services.llm_service import call_llm
from services.schema_provider import get_schema

logger = logging.getLogger(__name__)

CYPHER_PROMPT = """
你是一个宝可梦知识图谱的 Cypher 查询专家。根据用户的问题，生成对应的 Cypher 查询语句。

## 图谱 Schema
{schema}

## 示例
用户问："皮卡丘有什么属性？"
返回：MATCH (p:Pokemon {{name: "pikachu"}})-[:HAS_TYPE]->(t:Type) RETURN t.name

用户问："小火龙有什么特性？"
返回：MATCH (p:Pokemon {{name: "charmander"}})-[:HAS_ABILITY]->(a:Ability) RETURN a.name

用户问："喷火龙的体重是多少？"
返回：MATCH (p:Pokemon {{name: "charizard"}}) RETURN p.name, p.weight

用户问："火属性克制哪些属性？"
返回：MATCH (f:Type {{name: "fire"}})-[:EFFECTIVE_TO {{multiplier: 2.0}}]->(t:Type) RETURN t.name

用户问："什么属性克制水？"
返回：MATCH (f:Type)-[:EFFECTIVE_TO {{multiplier: 2.0}}]->(t:Type {{name: "water"}}) RETURN f.name

用户问："妙蛙种子如何进化？"
返回：MATCH (p:Pokemon {{name: "bulbasaur"}})-[:EVOLVES_TO]->(e) RETURN e.name

用户问："皮卡丘会什么招式？"
返回：MATCH (p:Pokemon {{name: "pikachu"}})-[:CAN_LEARN]->(m:Move) RETURN m.name LIMIT 10

用户问："哪些属性被火属性两倍克制？"
返回：MATCH (f:Type {{name: "fire"}})-[:EFFECTIVE_TO {{multiplier: 2.0}}]->(t:Type) RETURN t.name

## 用户问题
{question}

请只返回 Cypher 查询语句，不要包含其他内容。
""".strip()


def generate_cypher(question: str) -> str:
    """根据问题生成 Cypher

    Args:
        question: 用户问题（自然语言）

    Returns:
        Cypher 查询语句

    Raises:
        ValueError: 生成的内容不是有效的 Cypher 语句
    """
    prompt = CYPHER_PROMPT.format(
        schema=get_schema(),
        question=question
    )
    cypher = call_llm(prompt, temperature=0.1)

    # 清理 markdown 标记
    cypher = cypher.strip()
    cypher = re.sub(r'^```(?:cypher)?\s*', '', cypher, flags=re.IGNORECASE)
    cypher = cypher.rstrip('`').strip()

    # 只保留第一行（LLM 可能返回多行内容）
    lines = cypher.split('\n')
    cypher = lines[0].strip()

    if not cypher:
        raise ValueError("LLM 返回了空的 Cypher 语句")

    # 基本安全检查：必须是合法的 Cypher 开头
    valid_prefixes = ('MATCH', 'WITH', 'UNWIND', 'CALL', 'RETURN')
    if not cypher.upper().startswith(valid_prefixes):
        logger.warning(f"Generated non-Cypher content: {cypher[:100]}")
        raise ValueError(f"LLM 未返回有效的 Cypher 语句: {cypher[:200]}")

    logger.info(f"Generated Cypher: {cypher}")
    return cypher


if __name__ == "__main__":
    q = "皮卡丘有什么属性？"
    print(f"问题：{q}")
    print(f"生成 Cypher: {generate_cypher(q)}")
