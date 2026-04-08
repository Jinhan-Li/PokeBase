-- backend/data/cypher/import_can_learn.cypher
-- 创建 CAN_LEARN 关系

UNWIND $batch AS row
MATCH (p:Pokemon {id: row.pokemon_id})
MATCH (m:Move {name: row.move_name})
MERGE (p)-[r:CAN_LEARN]->(m)
SET r.learn_method = row.learn_method,
    r.level_learned_at = row.level_learned_at
