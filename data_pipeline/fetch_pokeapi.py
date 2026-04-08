# data_pipeline/fetch_pokeapi.py
"""从 PokeAPI 抓取 Pokemon 数据"""

import requests
import time
import json
from pathlib import Path


def fetch_pokemon(limit=10):
    """抓取前 N 只 Pokemon（先用 10 只测试）"""
    raw_dir = Path("backend/data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, limit + 1):
        path = raw_dir / f"pokemon_{i}.json"
        if path.exists():
            print(f"跳过已存在：pokemon_{i}")
            continue

        resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{i}")
        if resp.status_code == 200:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(resp.json(), f, ensure_ascii=False)
            print(f"✓ 抓取：pokemon_{i}")
        else:
            print(f"✗ 失败：pokemon_{i}")
        time.sleep(0.5)  # 限速，避免被 PokeAPI 限流


def fetch_types():
    """抓取 18 种属性"""
    raw_dir = Path("backend/data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, 19):
        path = raw_dir / f"type_{i}.json"
        if path.exists():
            continue

        resp = requests.get(f"https://pokeapi.co/api/v2/type/{i}")
        if resp.status_code == 200:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(resp.json(), f, ensure_ascii=False)
    print("✓ Type 抓取完成")


def fetch_abilities(limit=100):
    """抓取特性数据"""
    raw_dir = Path("backend/data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, limit + 1):
        path = raw_dir / f"ability_{i}.json"
        if path.exists():
            continue

        resp = requests.get(f"https://pokeapi.co/api/v2/ability/{i}")
        if resp.status_code == 200:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(resp.json(), f, ensure_ascii=False)
        time.sleep(0.3)

    print(f"✓ Ability 抓取完成（{limit}个）")


def fetch_moves(limit=100):
    """抓取招式数据"""
    raw_dir = Path("backend/data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    for i in range(1, limit + 1):
        path = raw_dir / f"move_{i}.json"
        if path.exists():
            continue

        resp = requests.get(f"https://pokeapi.co/api/v2/move/{i}")
        if resp.status_code == 200:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(resp.json(), f, ensure_ascii=False)
        time.sleep(0.3)

    print(f"✓ Move 抓取完成（{limit}个）")


if __name__ == "__main__":
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    print(f"开始抓取数据，Pokemon 数量限制：{limit}")
    fetch_pokemon(limit)
    fetch_types()
    fetch_abilities(50)  # 先抓 50 个测试
    fetch_moves(50)      # 先抓 50 个测试
    print("✓ 全部抓取完成")
