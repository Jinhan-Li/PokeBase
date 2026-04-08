# backend/services/schema_provider.py
"""提供图谱 Schema 信息给 LLM"""

SCHEMA_TEXT = """
图谱 Schema：
节点类型和属性：
- Pokemon {id, name, height, weight, base_experience}
- Type {id, name}
- Ability {id, name}
- Move {id, name, power, accuracy, pp, priority}

关系类型：
- (Pokemon)-[:HAS_TYPE]->(Type)
- (Pokemon)-[:HAS_ABILITY]->(Ability)
- (Pokemon)-[:CAN_LEARN]->(Move)
- (Pokemon)-[:EVOLVES_TO]->(Pokemon)
- (Pokemon)-[:EVOLVES_FROM]->(Pokemon)
- (Type)-[:EFFECTIVE_TO {multiplier}]->(Type)
  multiplier 值：2.0(双倍伤害), 0.5(一半伤害), 0.0(无效)
- (Move)-[:HAS_TYPE]->(Type)

注意：name 属性是英文小写（如 "pikachu", "fire"）
""".strip()


def get_schema() -> str:
    """获取 Schema 描述文本"""
    return SCHEMA_TEXT
