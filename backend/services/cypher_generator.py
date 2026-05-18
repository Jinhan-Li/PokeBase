# backend/services/cypher_generator.py
"""Generate read-only Cypher queries from natural-language questions."""

import logging
import re

from services.llm_service import call_llm
from services.schema_provider import get_schema

logger = logging.getLogger(__name__)

CYPHER_PROMPT = """
你是宝可梦知识图谱的 Cypher 查询专家。你的任务是把用户问题转换成一条只读 Cypher 查询。

硬性规则：
1. 只返回 Cypher，不要解释，不要 Markdown 代码块。
2. 只能使用下方 Schema 中存在的节点标签、关系类型和属性。
3. 所有 name 属性值必须是英文小写形式，例如 "pikachu"、"charizard"、"fire"、"thunderbolt"。
4. 不要编造不存在的关系。当前 Schema 没有进化关系；遇到进化问题时返回一条常量查询说明不可用。
5. 查询必须只读，只使用 MATCH、OPTIONAL MATCH、WITH、RETURN、ORDER BY、LIMIT、UNWIND 等查询语法。

## 图谱 Schema
{schema}

## 高质量 Cypher 示例

用户问："皮卡丘有什么属性？"
返回：MATCH (p:Pokemon {name: "pikachu"})-[:HAS_TYPE]->(t:Type) RETURN t.name

用户问："皮卡丘的全国图鉴编号、身高、体重和基础经验是多少？"
返回：MATCH (p:Pokemon {name: "pikachu"}) RETURN p.id AS id, p.height / 10.0 AS height_m, p.weight / 10.0 AS weight_kg, p.base_experience AS base_experience

用户问："小火龙有什么特性？"
返回：MATCH (p:Pokemon {name: "charmander"})-[:HAS_ABILITY]->(a:Ability) RETURN a.name

用户问："喷火龙的体重是多少？"
返回：MATCH (p:Pokemon {name: "charizard"}) RETURN p.name, p.weight / 10.0 AS weight_kg

用户问："火属性克制哪些属性？"
返回：MATCH (f:Type {name: "fire"})-[:DAMAGE_TO {multiplier: 2.0}]->(t:Type) RETURN t.name

用户问："什么属性克制水？"
返回：MATCH (f:Type)-[:DAMAGE_TO {multiplier: 2.0}]->(t:Type {name: "water"}) RETURN f.name

用户问："火属性打水属性是多少倍伤害？"
返回：MATCH (attacker:Type {name: "fire"})-[r:DAMAGE_TO]->(defender:Type {name: "water"}) RETURN attacker.name AS attacking_type, defender.name AS defending_type, r.multiplier AS multiplier

用户问："哪些宝可梦同时拥有草属性和毒属性？"
返回：MATCH (p:Pokemon)-[:HAS_TYPE]->(:Type {name: "grass"}) MATCH (p)-[:HAS_TYPE]->(:Type {name: "poison"}) RETURN DISTINCT p.name ORDER BY p.id LIMIT 50

用户问："皮卡丘会什么招式？"
返回：MATCH (p:Pokemon {name: "pikachu"})-[:CAN_LEARN]->(m:Move) RETURN m.name ORDER BY m.name LIMIT 20

用户问："皮卡丘能学会哪些电属性招式？"
返回：MATCH (p:Pokemon {name: "pikachu"})-[:CAN_LEARN]->(m:Move)-[:HAS_TYPE]->(t:Type {name: "electric"}) RETURN m.name, m.power, m.accuracy ORDER BY coalesce(m.power, 0) DESC, m.name LIMIT 20

用户问："喷火龙能学的火属性招式里威力最高的前 10 个是什么？"
返回：MATCH (p:Pokemon {name: "charizard"})-[:CAN_LEARN]->(m:Move)-[:HAS_TYPE]->(:Type {name: "fire"}) WHERE m.power IS NOT NULL RETURN m.name, m.power, m.accuracy ORDER BY m.power DESC, m.name LIMIT 10

用户问："十万伏特是什么属性的招式？"
返回：MATCH (m:Move {name: "thunderbolt"})-[:HAS_TYPE]->(t:Type) RETURN m.name, t.name

用户问："各属性分别有多少宝可梦？"
返回：MATCH (p:Pokemon)-[:HAS_TYPE]->(t:Type) RETURN t.name AS type, count(DISTINCT p) AS pokemon_count ORDER BY pokemon_count DESC, type

用户问："哪些属性对喷火龙造成双倍或更高伤害？"
返回：MATCH (p:Pokemon {name: "charizard"})-[:HAS_TYPE]->(defType:Type) MATCH (atk:Type)-[r:DAMAGE_TO]->(defType) WITH atk, collect(r.multiplier) AS multipliers WITH atk, reduce(total = 1.0, m IN multipliers | total * m) AS total_multiplier WHERE total_multiplier >= 2.0 RETURN atk.name AS attacking_type, total_multiplier ORDER BY total_multiplier DESC, attacking_type

用户问："哪些宝可梦可以学习威力大于 100 的电属性招式？"
返回：MATCH (p:Pokemon)-[:CAN_LEARN]->(m:Move)-[:HAS_TYPE]->(:Type {name: "electric"}) WHERE m.power > 100 RETURN DISTINCT p.name, collect(DISTINCT m.name) AS moves ORDER BY p.name LIMIT 50

用户问："妙蛙种子如何进化？"
返回：RETURN "当前数据库 Schema 没有进化关系数据，无法查询进化链。" AS message

## 用户问题
{question}

请只返回 Cypher 查询语句，不要包含其他内容。
""".strip()

READ_ONLY_PREFIXES = ("MATCH", "OPTIONAL MATCH", "WITH", "UNWIND", "RETURN")
FORBIDDEN_KEYWORDS = (
    "CREATE",
    "MERGE",
    "DELETE",
    "DETACH",
    "SET",
    "REMOVE",
    "DROP",
    "LOAD CSV",
    "CALL",
)


def _build_prompt(question: str) -> str:
    return (
        CYPHER_PROMPT
        .replace("{schema}", get_schema())
        .replace("{question}", question)
    )


def _strip_markdown(text: str) -> str:
    cypher = text.strip()
    cypher = re.sub(r'^```(?:cypher)?\s*', '', cypher, flags=re.IGNORECASE)
    cypher = re.sub(r'```\s*$', '', cypher).strip()
    lines = [line.strip() for line in cypher.splitlines() if line.strip()]
    return ' '.join(lines)


def _validate_read_only(cypher: str) -> None:
    normalized = re.sub(r'\s+', ' ', cypher).strip()
    upper = normalized.upper()

    if not normalized:
        raise ValueError("LLM 返回了空的 Cypher 语句")

    if not upper.startswith(READ_ONLY_PREFIXES):
        logger.warning("Generated non-Cypher content: %s", normalized[:100])
        raise ValueError(f"LLM 未返回有效的 Cypher 语句: {normalized[:200]}")

    for keyword in FORBIDDEN_KEYWORDS:
        pattern = r'(^|[^A-Z_])' + re.escape(keyword) + r'([^A-Z_]|$)'
        if re.search(pattern, upper):
            raise ValueError(f"LLM 返回了非只读 Cypher 语句，包含禁止关键字: {keyword}")


def generate_cypher(question: str) -> str:
    """Generate a read-only Cypher query for a natural-language question."""
    cypher = _strip_markdown(call_llm(_build_prompt(question), temperature=0.1))
    _validate_read_only(cypher)
    logger.info("Generated Cypher: %s", cypher)
    return cypher


if __name__ == "__main__":
    q = "皮卡丘有什么属性？"
    print(f"问题：{q}")
    print(f"生成 Cypher: {generate_cypher(q)}")
