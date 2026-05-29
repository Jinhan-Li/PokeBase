# backend/routers/chat.py
"""主问答接口：问题 → Cypher → 查询 → 回答"""

import logging

from fastapi import APIRouter

from models.chat_request import ChatRequest, ChatResponse
from services.cypher_generator import generate_cypher
from services.answer_generator import generate_answer
from services.neo4j_service import neo4j

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """主问答接口：问题 → Cypher → 查询 → 回答"""
    cypher = ""
    data = []
    error_msg = ""
    
    # 支持自愈的重试循环，最多 5 次
    for attempt in range(5):
        try:
            cypher = generate_cypher(req.question, error_msg)
            data = neo4j.execute(cypher)
            break  # 查询成功则退出重试
        except Exception as e:
            logger.warning(f"Cypher attempt {attempt + 1} failed: {e}")
            error_msg = str(e)
            if attempt == 4:
                # 5 次全失败后退回失败提示
                logger.error(f"Failed to generate and execute Cypher after 5 attempts for question: {req.question}")
                return ChatResponse(
                    answer=f"查询执行失败，请检查问题表述。连续5次尝试后的详细信息：{e}",
                    cypher=cypher,
                    data=[]
                )

    # 3. 生成回答
    try:
        answer = generate_answer(req.question, cypher, data)
    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        # 降级：直接展示查询结果
        if not data:
            answer = "未找到相关信息。"
        else:
            import json
            answer = f"查询结果：{json.dumps(data, ensure_ascii=False)[:200]}..."

    return ChatResponse(answer=answer, cypher=cypher, data=data)
