# backend/routers/chat.py
"""主问答接口：问题 → Cypher → 查询 → 回答"""

from fastapi import APIRouter
from models.chat_request import ChatRequest, ChatResponse
from services.cypher_generator import generate_cypher
from services.answer_generator import generate_answer
from services.neo4j_service import neo4j

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """主问答接口：问题 → Cypher → 查询 → 回答"""
    # 1. 生成 Cypher
    cypher = generate_cypher(req.question)

    # 2. 执行查询
    try:
        data = neo4j.execute(cypher)
    except Exception as e:
        return ChatResponse(
            answer=f"查询执行失败：{e}",
            cypher=cypher,
            data=[]
        )

    # 3. 生成回答
    answer = generate_answer(req.question, data)

    return ChatResponse(answer=answer, cypher=cypher, data=data)
