# backend/models/query_request.py
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Cypher 查询请求模型"""
    cypher: str
    parameters: dict = {}
