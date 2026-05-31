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
4. 查询必须只读，只使用 MATCH、OPTIONAL MATCH、WHERE、WITH、RETURN、ORDER BY、LIMIT、UNWIND、collect、count、min、max、sum、reduce、DISTINCT 等查询语法。
5. 禁止使用 CREATE、MERGE、DELETE、SET、REMOVE、DROP、LOAD CSV、CALL dbms 等写入或管理语句。
6. methods、versions、levels 是 CAN_LEARN 关系上的列表属性，不能写成 r.method、r.version、r.level。
7. DAMAGE_TO 的方向是：攻击方属性 -> 防守方属性。
8. 如果用户问“非本系”，表示招式属性不属于宝可梦自身任何属性。
9. 如果没有明确的 DAMAGE_TO 关系，默认倍率按 1.0 处理。


# 图谱 Schema
{schema}

# 示例：

用户问："小火龙有什么特性？"
返回：
MATCH (p:Pokemon {{name: "charmander"}})-[:HAS_ABILITY]->(a:Ability)
RETURN a.name

用户问："喷火龙的体重是多少？"
返回：
MATCH (p:Pokemon {{name: "charizard"}})
RETURN p.name, p.weight / 10.0 AS weight_kg

用户问："皮卡丘是什么属性？"
返回：
MATCH (p:Pokemon {{name: "pikachu"}})-[r:HAS_TYPE]->(t:Type)
RETURN p.name, t.name, r.slot
ORDER BY r.slot

用户问："火属性克制哪些属性？"
返回：
MATCH (f:Type {{name: "fire"}})-[:DAMAGE_TO {{multiplier: 2.0}}]->(t:Type)
RETURN t.name
ORDER BY t.id

用户问："什么属性克制水属性？"
返回：
MATCH (f:Type)-[:DAMAGE_TO {{multiplier: 2.0}}]->(t:Type {{name: "water"}})
RETURN f.name
ORDER BY f.id

用户问："哪些宝可梦可以通过升级学会十万伏特？"
返回：
MATCH (p:Pokemon)-[r:CAN_LEARN]->(m:Move {{name: "thunderbolt"}})
WHERE 'level-up' IN r.methods
RETURN p.name, r.levels
ORDER BY p.id

用户问："第一世代有哪些火属性宝可梦？"
返回：
MATCH (p:Pokemon)-[:HAS_TYPE]->(t:Type {{name: "fire"}})
WHERE p.id >= 1 AND p.id <= 151
RETURN p.id, p.name
ORDER BY p.id

用户问："第一世代中，有哪些宝可梦可以通过升级学到威力大于90，且非本系的伤害类招式？"
返回：
MATCH (p:Pokemon)-[:HAS_TYPE]->(pt:Type)
WHERE p.id >= 1 AND p.id <= 151
WITH p, collect(pt.name) AS pokemon_types
MATCH (p)-[r:CAN_LEARN]->(m:Move)-[:HAS_TYPE]->(mt:Type)
WHERE 'level-up' IN r.methods
  AND m.power > 90
  AND m.damage_class <> 'status'
  AND NOT mt.name IN pokemon_types
RETURN DISTINCT p.id, p.name, m.name, m.power, m.damage_class, mt.name AS move_type
ORDER BY p.id, m.power DESC

用户问："威力大于等于120的招式中，哪些宝可梦能通过升级最早学会？"
返回：
MATCH (p:Pokemon)-[r:CAN_LEARN]->(m:Move)
WHERE m.power >= 120
  AND 'level-up' IN r.methods
  AND size(r.methods) = size(r.levels)
UNWIND range(0, size(r.methods) - 1) AS i
WITH p, m, r.methods[i] AS method, r.levels[i] AS lvl
WHERE method = 'level-up' AND lvl > 0
WITH m, min(lvl) AS min_level
MATCH (p2:Pokemon)-[r2:CAN_LEARN]->(m)
WHERE 'level-up' IN r2.methods
  AND size(r2.methods) = size(r2.levels)
UNWIND range(0, size(r2.methods) - 1) AS j
WITH m, min_level, p2, r2.methods[j] AS method, r2.levels[j] AS lvl
WHERE method = 'level-up' AND lvl = min_level
RETURN m.name AS move, m.power AS power, min_level AS min_level, collect(DISTINCT p2.name) AS pokemon
ORDER BY min_level ASC, power DESC
LIMIT 10

用户问："有哪些招式在红蓝版本可以学习，但在剑盾版本不能学习？"
返回：
MATCH (p:Pokemon)-[r:CAN_LEARN]->(m:Move)
WHERE 'red-blue' IN r.versions
  AND NOT 'sword-shield' IN r.versions
WITH p, collect(DISTINCT m.name) AS lost_moves
WHERE size(lost_moves) > 0
RETURN p.id, p.name, lost_moves, size(lost_moves) AS lost_move_count
ORDER BY lost_move_count DESC, p.id
LIMIT 10

用户问："哪只宝可梦掌握的伤害类招式覆盖属性最多？"
返回：
MATCH (p:Pokemon)-[:CAN_LEARN]->(m:Move)-[:HAS_TYPE]->(t:Type)
WHERE m.power IS NOT NULL
  AND m.power > 0
  AND m.damage_class <> 'status'
RETURN p.id, p.name, count(DISTINCT t.name) AS covered_types, collect(DISTINCT t.name) AS type_list
ORDER BY covered_types DESC, p.id
LIMIT 5


用户问："体重前20的宝可梦中，谁会最多先制招式？"
返回：
MATCH (p:Pokemon)
WHERE p.weight IS NOT NULL
WITH p
ORDER BY p.weight DESC
LIMIT 20
OPTIONAL MATCH (p)-[:CAN_LEARN]->(m:Move)
WHERE m.priority > 0
RETURN p.id, p.name, p.weight, count(DISTINCT m) AS priority_move_count, collect(DISTINCT m.name) AS priority_moves
ORDER BY priority_move_count DESC, p.weight DESC

用户问："哪些宝可梦有四倍弱点，但能学会克制该弱点属性的高威力招式？"
返回：
MATCH (p:Pokemon)-[:HAS_TYPE]->(def:Type)
MATCH (weakness:Type)
OPTIONAL MATCH (weakness)-[r:DAMAGE_TO]->(def)
WITH p, weakness, collect(coalesce(r.multiplier, 1.0)) AS multipliers
WITH p, weakness, reduce(total = 1.0, x IN multipliers | total * x) AS received_multiplier
WHERE received_multiplier >= 4.0
MATCH (p)-[:CAN_LEARN]->(m:Move)-[:HAS_TYPE]->(mt:Type)
OPTIONAL MATCH (mt)-[counter:DAMAGE_TO]->(weakness)
WITH p, weakness, received_multiplier, m, mt, coalesce(counter.multiplier, 1.0) AS counter_multiplier
WHERE m.power >= 80
  AND m.damage_class <> 'status'
  AND counter_multiplier >= 2.0
RETURN DISTINCT p.name AS pokemon, weakness.name AS quad_weakness, received_multiplier, m.name AS counter_move, m.power AS power, mt.name AS move_type, counter_multiplier
ORDER BY received_multiplier DESC, power DESC

用户问：
{question}

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


def _build_prompt(question: str, error_msg: str = "") -> str:
    prompt = (
        CYPHER_PROMPT
        .replace("{schema}", get_schema())
        .replace("{question}", question)
    )
    if error_msg:
        prompt += f"\n\n注意：你之前生成的 Cypher 查询执行报错了，错误信息如下：\n{error_msg}\n请你修正并重新生成查询语句。"
    return prompt


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


def generate_cypher(question: str, error_msg: str = "") -> str:
    """Generate a read-only Cypher query for a natural-language question."""
    cypher = _strip_markdown(call_llm(_build_prompt(question, error_msg), temperature=0.1))
    _validate_read_only(cypher)
    logger.info("Generated Cypher: %s", cypher)
    return cypher


if __name__ == "__main__":
    q = "皮卡丘有什么属性？"
    print(f"问题：{q}")
    print(f"生成 Cypher: {generate_cypher(q)}")
