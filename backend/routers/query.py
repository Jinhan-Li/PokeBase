# backend/routers/query.py
"""直接 Cypher 查询接口（调试用）"""

from fastapi import APIRouter
from models.query_request import QueryRequest
from services.neo4j_service import neo4j

router = APIRouter()


@router.post("/query")
def query_database(req: QueryRequest):
    """直接执行 Cypher 查询（调试用）"""
    data = neo4j.execute(req.cypher, req.parameters)
    return {"data": data}
