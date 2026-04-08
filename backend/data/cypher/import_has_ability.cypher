-- backend/data/cypher/import_has_ability.cypher
-- 创建 HAS_ABILITY 关系

UNWIND $batch AS row
MATCH (p:Pokemon {id: row.pokemon_id})
MATCH (a:Ability {name: row.ability_name})
MERGE (p)-[r:HAS_ABILITY]->(a)
SET r.slot = row.slot,
    r.is_hidden = row.is_hidden
