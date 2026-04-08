# data_pipeline/transform.py
"""将 PokeAPI 原始 JSON 转换为 Neo4j 导入格式"""

import json
from pathlib import Path


def transform_pokemon():
    """将原始 Pokemon JSON 转换为 Neo4j 导入格式"""
    raw_dir = Path("backend/data/raw")
    processed_dir = Path("backend/data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    pokemon_nodes = []
    has_type_relations = []
    has_ability_relations = []
    can_learn_relations = []

    for f in sorted(raw_dir.glob("pokemon_*.json")):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)

        # 提取 Pokemon 节点
        pokemon_nodes.append({
            "id": data["id"],
            "name": data["name"],
            "height": data["height"],
            "weight": data["weight"],
            "base_experience": data["base_experience"]
        })

        # 提取 HAS_TYPE 关系
        for slot, type_info in enumerate(data["types"], 1):
            has_type_relations.append({
                "pokemon_id": data["id"],
                "type_name": type_info["type"]["name"],
                "slot": slot
            })

        # 提取 HAS_ABILITY 关系
        for slot, ability_info in enumerate(data["abilities"], 1):
            has_ability_relations.append({
                "pokemon_id": data["id"],
                "ability_name": ability_info["ability"]["name"],
                "slot": slot,
                "is_hidden": ability_info.get("is_hidden", False)
            })

        # 提取 CAN_LEARN 关系（升级学习）
        for move_data in data["moves"]:
            version_details = move_data.get("version_group_details", [])
            if version_details:
                # 取第一个学习途径
                learn_method = version_details[0].get("move_learn_method", {}).get("name", "unknown")
                level_learned_at = version_details[0].get("level_learned_at", 0)
                can_learn_relations.append({
                    "pokemon_id": data["id"],
                    "move_name": move_data["move"]["name"],
                    "learn_method": learn_method,
                    "level_learned_at": level_learned_at
                })

    # 保存
    with open(processed_dir / "pokemon_nodes.json", "w", encoding="utf-8") as f:
        json.dump(pokemon_nodes, f, ensure_ascii=False, indent=2)

    with open(processed_dir / "has_type_relations.json", "w", encoding="utf-8") as f:
        json.dump(has_type_relations, f, ensure_ascii=False, indent=2)

    with open(processed_dir / "has_ability_relations.json", "w", encoding="utf-8") as f:
        json.dump(has_ability_relations, f, ensure_ascii=False, indent=2)

    with open(processed_dir / "can_learn_relations.json", "w", encoding="utf-8") as f:
        json.dump(can_learn_relations, f, ensure_ascii=False, indent=2)

    print(f"✓ Pokemon 转换完成：{len(pokemon_nodes)}只，关系：{len(has_type_relations)}条")


def transform_types():
    """转换 Type 数据"""
    raw_dir = Path("backend/data/raw")
    processed_dir = Path("backend/data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    type_nodes = []
    type_effective_relations = []

    for f in sorted(raw_dir.glob("type_*.json")):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)

        type_nodes.append({
            "id": data["id"],
            "name": data["name"]
        })

        # 克制关系
        damage_relations = data.get("damage_relations", {})

        # 双倍伤害
        for target in damage_relations.get("double_damage_to", []):
            type_effective_relations.append({
                "from_type": data["name"],
                "to_type": target["name"],
                "multiplier": 2.0
            })

        # 一半伤害
        for target in damage_relations.get("half_damage_to", []):
            type_effective_relations.append({
                "from_type": data["name"],
                "to_type": target["name"],
                "multiplier": 0.5
            })

        # 无效
        for target in damage_relations.get("no_damage_to", []):
            type_effective_relations.append({
                "from_type": data["name"],
                "to_type": target["name"],
                "multiplier": 0.0
            })

    with open(processed_dir / "type_nodes.json", "w", encoding="utf-8") as f:
        json.dump(type_nodes, f, ensure_ascii=False, indent=2)

    with open(processed_dir / "type_effective_relations.json", "w", encoding="utf-8") as f:
        json.dump(type_effective_relations, f, ensure_ascii=False, indent=2)

    print(f"✓ Type 转换完成：{len(type_nodes)}个，克制关系：{len(type_effective_relations)}条")


def transform_abilities():
    """转换 Ability 数据"""
    raw_dir = Path("backend/data/raw")
    processed_dir = Path("backend/data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    ability_nodes = []

    for f in sorted(raw_dir.glob("ability_*.json")):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)

        ability_nodes.append({
            "id": data["id"],
            "name": data["name"]
        })

    with open(processed_dir / "ability_nodes.json", "w", encoding="utf-8") as f:
        json.dump(ability_nodes, f, ensure_ascii=False, indent=2)

    print(f"✓ Ability 转换完成：{len(ability_nodes)}个")


def transform_moves():
    """转换 Move 数据"""
    raw_dir = Path("backend/data/raw")
    processed_dir = Path("backend/data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    move_nodes = []

    for f in sorted(raw_dir.glob("move_*.json")):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)

        move_nodes.append({
            "id": data["id"],
            "name": data["name"],
            "power": data.get("power"),
            "accuracy": data.get("accuracy"),
            "pp": data.get("pp"),
            "priority": data.get("priority"),
            "type_name": data.get("type", {}).get("name"),
            "damage_class": data.get("damage_class", {}).get("name") if data.get("damage_class") else None
        })

    with open(processed_dir / "move_nodes.json", "w", encoding="utf-8") as f:
        json.dump(move_nodes, f, ensure_ascii=False, indent=2)

    print(f"✓ Move 转换完成：{len(move_nodes)}个")


if __name__ == "__main__":
    transform_pokemon()
    transform_types()
    transform_abilities()
    transform_moves()
    print("✓ 全部转换完成")
