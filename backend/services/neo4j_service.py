# backend/services/neo4j_service.py
"""Neo4j 图数据库服务"""

import logging

from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logger = logging.getLogger(__name__)


class Neo4jService:
    """Neo4j 图数据库服务"""

    def __init__(self):
        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_pool_size=50,
        )

    def execute(self, cypher: str, params: dict = None):
        """执行 Cypher 查询"""
        try:
            with self.driver.session() as session:
                result = session.run(cypher, params or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Cypher execution failed: {cypher}\nError: {e}")
            raise

    def close(self):
        """关闭驱动连接"""
        self.driver.close()


# 全局单例
neo4j = Neo4jService()
