# backend/services/schema_provider.py
"""Provide graph schema text for LLM prompts.

docs/schema.md is the authoritative schema document for the current database.
Loading it here keeps runtime prompts aligned with the maintained schema docs.
"""

from functools import lru_cache
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "docs" / "schema.md"

FALLBACK_SCHEMA_TEXT = """
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


@lru_cache(maxsize=1)
def get_schema() -> str:
    """Return the authoritative graph schema text."""
    try:
        text = SCHEMA_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return FALLBACK_SCHEMA_TEXT
    return text or FALLBACK_SCHEMA_TEXT
