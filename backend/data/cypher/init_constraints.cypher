-- backend/data/cypher/init_constraints.cypher
-- 创建唯一约束

CREATE CONSTRAINT pokemon_id IF NOT EXISTS
FOR (p:Pokemon) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT type_id IF NOT EXISTS
FOR (t:Type) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT ability_id IF NOT EXISTS
FOR (a:Ability) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT move_id IF NOT EXISTS
FOR (m:Move) REQUIRE m.id IS UNIQUE;
