-- backend/data/cypher/import_has_type.cypher
-- 创建 HAS_TYPE 关系

UNWIND $batch AS row
MATCH (p:Pokemon {id: row.pokemon_id})
MATCH (t:Type {name: row.type_name})
MERGE (p)-[r:HAS_TYPE]->(t)
SET r.slot = row.slot
