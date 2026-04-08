-- backend/data/cypher/import_ability_nodes.cypher
-- 创建 Ability 节点

UNWIND $batch AS row
MERGE (a:Ability {id: row.id})
SET a.name = row.name
