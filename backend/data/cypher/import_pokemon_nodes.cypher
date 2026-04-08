-- backend/data/cypher/import_pokemon_nodes.cypher
-- 创建 Pokemon 节点

UNWIND $batch AS row
MERGE (p:Pokemon {id: row.id})
SET p.name = row.name,
    p.height = row.height,
    p.weight = row.weight,
    p.base_experience = row.base_experience
