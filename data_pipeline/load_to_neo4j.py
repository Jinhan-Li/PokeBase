# data_pipeline/load_to_neo4j.py
"""将处理后的数据导入 Neo4j"""

import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# 从环境变量读取配置
URI = os.getenv("NEO4J_URI", "neo4j+s://98695523.databases.neo4j.io")
AUTH = (
    os.getenv("NEO4J_USER", "98695523"),
    os.getenv("NEO4J_PASSWORD")
)


def load_cypher_file(filename):
    """执行 Cypher 文件（不带数据）"""
    cypher_dir = Path("backend/data/cypher")
    with open(cypher_dir / filename, encoding="utf-8") as f:
        cypher = f.read()

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            session.run(cypher)
    print(f"✓ 执行：{filename}")


def load_with_data(filename, data_file):
    """执行带数据的 Cypher（批量导入）"""
    cypher_dir = Path("backend/data/cypher")
    processed_dir = Path("backend/data/processed")

    with open(processed_dir / data_file, encoding="utf-8") as f:
        data = json.load(f)

    with open(cypher_dir / filename, encoding="utf-8") as f:
        cypher = f.read()

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            # 分批导入，每批 50 条
            for i in range(0, len(data), 50):
                batch = data[i:i+50]
                session.run(cypher, batch=batch)
    print(f"✓ 导入：{filename} ({len(data)} 条)")


if __name__ == "__main__":
    print("开始导入数据到 Neo4j...")

    # 1. 约束
    print("\n[1/8] 创建约束...")
    load_cypher_file("init_constraints.cypher")

    # 2. Type 节点
    print("\n[2/8] 导入 Type 节点...")
    load_with_data("import_type_nodes.cypher", "type_nodes.json")

    # 3. Pokemon 节点
    print("\n[3/8] 导入 Pokemon 节点...")
    load_with_data("import_pokemon_nodes.cypher", "pokemon_nodes.json")

    # 4. Ability 节点
    print("\n[4/8] 导入 Ability 节点...")
    load_with_data("import_ability_nodes.cypher", "ability_nodes.json")

    # 5. Move 节点
    print("\n[5/8] 导入 Move 节点...")
    load_with_data("import_move_nodes.cypher", "move_nodes.json")

    # 6. HAS_TYPE 关系
    print("\n[6/8] 导入 HAS_TYPE 关系...")
    load_with_data("import_has_type.cypher", "has_type_relations.json")

    # 7. HAS_ABILITY 关系
    print("\n[7/8] 导入 HAS_ABILITY 关系...")
    load_with_data("import_has_ability.cypher", "has_ability_relations.json")

    # 8. CAN_LEARN 关系
    print("\n[8/8] 导入 CAN_LEARN 关系...")
    load_with_data("import_can_learn.cypher", "can_learn_relations.json")

    # 9. 属性克制关系
    print("\n[9/9] 导入 EFFECTIVE_TO 关系...")
    load_with_data("import_type_effective.cypher", "type_effective_relations.json")

    print("\n✓ 导入完成")
