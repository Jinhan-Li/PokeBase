-- backend/data/cypher/import_type_nodes.cypher
-- 创建 Type 节点

UNWIND $batch AS row
MERGE (t:Type {id: row.id})
SET t.name = row.name
