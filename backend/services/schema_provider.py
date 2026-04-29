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
- (Move)-[:HAS_TYPE]->(Type)
- (Type)-[:DAMAGE_TO {multiplier}]->(Type)
  multiplier 值：2.0(双倍伤害), 0.5(一半伤害), 0.0(无效)

注意：
- name 属性是英文小写（如 "pikachu", "fire"）
- 当前数据库中没有进化关系（EVOLVES_TO）数据
""".strip()


def get_schema() -> str:
    """获取 Schema 描述文本"""
    return SCHEMA_TEXT
