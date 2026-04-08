-- backend/data/cypher/import_type_effective.cypher
-- 创建 EFFECTIVE_TO 关系（属性克制）

UNWIND $batch AS row
MATCH (from:Type {name: row.from_type})
MATCH (to:Type {name: row.to_type})
MERGE (from)-[r:EFFECTIVE_TO]->(to)
SET r.multiplier = row.multiplier
