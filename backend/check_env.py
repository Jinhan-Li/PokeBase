#!/usr/bin/env python
# backend/check_env.py
"""检查运行环境是否就绪"""

import sys
import os
from pathlib import Path

# 添加到路径以便导入 config
sys.path.insert(0, str(Path(__file__).parent))


def check_env():
    errors = []

    # 1. 检查.env 文件
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        errors.append("缺少.env 文件，请从.env.example 复制并配置")
    else:
        print("[OK] .env 文件存在")

    # 2. 检查环境变量
    from dotenv import load_dotenv
    load_dotenv(env_file)

    if not os.getenv("NEO4J_PASSWORD"):
        errors.append("NEO4J_PASSWORD 未设置")
    else:
        print("[OK] NEO4J_PASSWORD 已配置")

    if not os.getenv("DASHSCOPE_API_KEY"):
        errors.append("DASHSCOPE_API_KEY 未设置")
    else:
        print("[OK] DASHSCOPE_API_KEY 已配置")

    # 3. 检查 Neo4j 连接
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "neo4j+s://98695523.databases.neo4j.io"),
            auth=(os.getenv("NEO4J_USER", "98695523"), os.getenv("NEO4J_PASSWORD"))
        )
        driver.verify_connectivity()
        driver.close()
        print("[OK] Neo4j 连接成功")
    except Exception as e:
        errors.append(f"Neo4j 连接失败：{e}")

    # 4. 检查依赖
    try:
        import openai
        print("[OK] openai 库已安装")
    except ImportError:
        errors.append("openai 库未安装，请运行 pip install -r requirements.txt")

    try:
        import fastapi
        print("[OK] fastapi 库已安装")
    except ImportError:
        errors.append("fastapi 库未安装，请运行 pip install -r requirements.txt")

    try:
        import neo4j
        print("[OK] neo4j 库已安装")
    except ImportError:
        errors.append("neo4j 库未安装，请运行 pip install -r requirements.txt")

    if errors:
        print("\n[ERROR] 错误：")
        for err in errors:
            print(f"  [FAIL] {err}")
        print("\n请先解决以上问题，然后重新运行 check_env.py")
        sys.exit(1)
    else:
        print("\n[DONE] 所有检查通过，环境就绪！")
        print("\n下一步：")
        print("  1. 数据导入：cd data_pipeline && python run_pipeline.py 10")
        print("  2. 启动后端：cd backend && uvicorn main:app --reload")
        print("  3. 启动前端：cd frontend && npm install && npm run dev")


if __name__ == "__main__":
    check_env()
