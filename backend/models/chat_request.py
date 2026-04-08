# backend/models/chat_request.py
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """聊天请求模型"""
    question: str


class ChatResponse(BaseModel):
    """聊天响应模型"""
    answer: str              # 自然语言回答
    cypher: str              # 生成的 Cypher 查询（透明展示给用户）
    data: list[dict]         # Neo4j 查询原始结果
