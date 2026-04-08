# data_pipeline/run_pipeline.py
"""一键执行数据采集→转换→导入"""

import sys


def run_pipeline(limit=10):
    """运行完整的数据管线

    Args:
        limit: Pokemon 数量限制（默认 10 只测试）
    """
    print(f"=== 宝可梦数据管线 ===")
    print(f"Pokemon 数量限制：{limit}")
    print()

    # 步骤 1: 抓取数据
    print("=" * 40)
    print("步骤 1: 从 PokeAPI 抓取数据")
    print("=" * 40)
    from fetch_pokeapi import fetch_pokemon, fetch_types, fetch_abilities, fetch_moves
    fetch_pokemon(limit)
    fetch_types()
    fetch_abilities(limit)
    fetch_moves(limit)
    print()

    # 步骤 2: 转换数据
    print("=" * 40)
    print("步骤 2: 转换数据格式")
    print("=" * 40)
    from transform import transform_pokemon, transform_types, transform_abilities, transform_moves
    transform_pokemon()
    transform_types()
    transform_abilities()
    transform_moves()
    print()

    # 步骤 3: 导入 Neo4j
    print("=" * 40)
    print("步骤 3: 导入 Neo4j")
    print("=" * 40)
    from load_to_neo4j import run
    run()


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    run_pipeline(limit)
