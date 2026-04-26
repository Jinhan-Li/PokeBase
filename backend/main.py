# backend/main.py
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import query, chat, import_data
from services.neo4j_service import neo4j

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Pokemon KG API", description="宝可梦知识图谱问答系统")


@app.on_event("startup")
def startup_event():
    logger.info("Pokemon KG API started")


@app.on_event("shutdown")
def shutdown_event():
    neo4j.close()
    logger.info("Neo4j connection closed")

# CORS 配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(import_data.router, prefix="/api", tags=["import"])


@app.get("/api/health")
def health():
    """健康检查接口"""
    return {"status": "ok", "service": "pokemon-kg"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
