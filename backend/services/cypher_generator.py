# backend/services/cypher_generator.py
"""根据用户问题生成 Cypher 查询语句"""

from services.llm_service import call_llm
from services.schema_provider import get_schema

CYPHER_PROMPT = """
你是一个宝可梦知识图谱的 Cypher 查询专家。根据用户的问题，生成对应的 Cypher 查询语句。

## 图谱 Schema
{schema}

## 示例
用户问："皮卡丘有什么属性？"
返回：MATCH (p:Pokemon {{name: "pikachu"}})-[:HAS_TYPE]->(t:Type) RETURN t.name

用户问："火属性克制哪些属性？"
返回：MATCH (f:Type {{name: "fire"}})-[:EFFECTIVE_TO {{multiplier: 2.0}}]->(t:Type) RETURN t.name

用户问："哪些宝可梦克制火属性？"
返回：MATCH (fire:Type {{name: "fire"}})<-[:EFFECTIVE_TO {{multiplier: 2.0}}]-(p:Pokemon)-[:HAS_TYPE]->(t:Type) RETURN p.name

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
    """
    prompt = CYPHER_PROMPT.format(
        schema=get_schema(),
        question=question
    )
    cypher = call_llm(prompt, temperature=0.1)
    # 清理可能的 markdown 标记
    cypher = cypher.strip().replace("```cypher", "").replace("```", "").strip()
    return cypher


if __name__ == "__main__":
    q = "皮卡丘有什么属性？"
    print(f"问题：{q}")
    print(f"生成 Cypher: {generate_cypher(q)}")
