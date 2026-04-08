# backend/routers/import_data.py
"""数据导入接口（开发调试用）"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/import")
def import_data(entities: list[str] = None, limit: int = 151):
    """触发数据导入流程（开发用）

    Args:
        entities: 要导入的实体类型列表 ["pokemon", "type", "ability", "move"]
        limit: Pokemon 数量限制（默认 151 只）
    """
    # TODO: 实现数据导入逻辑
    # 目前需要手动运行 data_pipeline/run_pipeline.py
    return {
        "status": "ok",
        "message": "请手动运行 data_pipeline/run_pipeline.py 进行数据导入",
        "entities": entities or ["pokemon", "type"],
        "limit": limit
    }


@router.get("/schema")
def get_schema():
    """获取当前图谱 Schema 信息"""
    from services.schema_provider import get_schema
    return {
        "schema": get_schema(),
        "nodes": ["Pokemon", "Type", "Ability", "Move"],
        "relationships": [
            "HAS_TYPE", "HAS_ABILITY", "CAN_LEARN",
            "EVOLVES_TO", "EVOLVES_FROM", "EFFECTIVE_TO"
        ]
    }
