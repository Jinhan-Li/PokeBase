# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j Aura 云数据库配置
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://98695523.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "98695523")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")  # 必须从环境变量读取

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")
