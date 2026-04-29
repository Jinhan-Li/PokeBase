# backend/routers/query.py
"""直接 Cypher 查询接口（调试用）"""

import logging

from fastapi import APIRouter, HTTPException

from models.query_request import QueryRequest
from services.neo4j_service import neo4j

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query")
def query_database(req: QueryRequest):
    """直接执行 Cypher 查询（调试用）"""
    try:
        data = neo4j.execute(req.cypher, req.parameters)
        return {"data": data}
    except Exception as e:
        logger.error(f"Query failed: {req.cypher}\nError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
