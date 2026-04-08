-- backend/data/cypher/import_move_nodes.cypher
-- 创建 Move 节点

UNWIND $batch AS row
MERGE (m:Move {id: row.id})
SET m.name = row.name,
    m.power = row.power,
    m.accuracy = row.accuracy,
    m.pp = row.pp,
    m.priority = row.priority,
    m.damage_class = row.damage_class
