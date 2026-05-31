import os
import json
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

CACHE_BASE_DIR = "./cache"
POKEMON_DIR = os.path.join(CACHE_BASE_DIR, "pokemon")
MOVE_DIR = os.path.join(CACHE_BASE_DIR, "move")

class PokemonTopologyBuilder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def load_json(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ==========================================
    # Validation & Missing Data Detection
    # ==========================================

    def get_processed_pokemon_ids(self):
        """
        Query Neo4j to find which Pokemon ALREADY have relationships.
        Since execute_write is atomic, if HAS_TYPE exists, all relations for this PM exist.
        """
        query = "MATCH (p:Pokemon)-[:HAS_TYPE]->() RETURN DISTINCT p.id AS id"
        with self.driver.session() as session:
            result = session.run(query)
            return {record["id"] for record in result if record["id"] is not None}

    def get_processed_move_ids(self):
        """Query Neo4j to find which Moves ALREADY have HAS_TYPE relationships."""
        query = "MATCH (m:Move)-[:HAS_TYPE]->() RETURN DISTINCT m.id AS id"
        with self.driver.session() as session:
            result = session.run(query)
            return {record["id"] for record in result if record["id"] is not None}

    # ==========================================
    # Relationship Parsers & Builders
    # ==========================================

    def build_pokemon_relations(self):
        processed_ids = self.get_processed_pokemon_ids()
        print(f"\n[*] Building Pokemon Relations. Already processed: {len(processed_ids)}")
        
        # Ensure we process files in numerical order (1.json, 2.json...) for better logging
        files =[f for f in os.listdir(POKEMON_DIR) if f.endswith('.json')]
        files.sort(key=lambda x: int(x.split('.')[0]))

        for filename in files:
            poke_id = int(filename.split('.')[0])
            
            # --- SKIP LOGIC (Idempotency) ---
            if poke_id in processed_ids:
                continue
                
            data = self.load_json(os.path.join(POKEMON_DIR, filename))
            
            # 1. Parse Types
            types_payload = [{'name': t['type']['name'], 'slot': t['slot']} for t in data['types']]
            
            # 2. Parse Abilities
            abilities_payload =[
                {'name': a['ability']['name'], 'is_hidden': a['is_hidden'], 'slot': a['slot']} 
                for a in data['abilities']
            ]
            
            # 3. Parse Moves
            moves_payload = []
            for m in data['moves']:
                move_name = m['move']['name']
                versions, methods, levels = [], [], []
                for vgd in m['version_group_details']:
                    versions.append(vgd['version_group']['name'])
                    methods.append(vgd['move_learn_method']['name'])
                    levels.append(vgd['level_learned_at'])
                moves_payload.append({
                    'name': move_name, 'versions': versions, 'methods': methods, 'levels': levels
                })

            # --- SAFE EXECUTION ---
            try:
                with self.driver.session() as session:
                    session.execute_write(self._cypher_create_pm_relations, poke_id, types_payload, abilities_payload, moves_payload)
                
                if poke_id % 50 == 0:
                    print(f"    [+] Successfully processed relations for Pokemon ID: {poke_id}")
            except Exception as e:
                print(f"    [-] CRITICAL ERROR processing Pokemon ID {poke_id}: {e}")
                # It continues to the next Pokemon even if one fails

        print("[*] Pokemon relations phase completed.")

    def build_move_relations(self):
        processed_ids = self.get_processed_move_ids()
        print(f"\n[*] Building Move Relations. Already processed: {len(processed_ids)}")
        
        files =[f for f in os.listdir(MOVE_DIR) if f.endswith('.json')]
        files.sort(key=lambda x: int(x.split('.')[0]))

        for filename in files:
            move_id = int(filename.split('.')[0])
            
            if move_id in processed_ids:
                continue
                
            data = self.load_json(os.path.join(MOVE_DIR, filename))
            type_name = data['type']['name']
            
            try:
                with self.driver.session() as session:
                    session.execute_write(self._cypher_create_move_relations, move_id, type_name)
                
                if move_id % 100 == 0:
                    print(f"    [+] Successfully processed relations for Move ID: {move_id}")
            except Exception as e:
                print(f"    [-] CRITICAL ERROR processing Move ID {move_id}: {e}")

        print("[*] Move relations phase completed.")

    # ==========================================
    # Cypher Transactions
    # ==========================================

    @staticmethod
    def _cypher_create_pm_relations(tx, poke_id, types, abilities, moves):
        if types:
            tx.run("""
            MATCH (p:Pokemon {id: $poke_id})
            UNWIND $types AS type_data
            MATCH (t:Type {name: type_data.name})
            MERGE (p)-[r:HAS_TYPE]->(t)
            SET r.slot = type_data.slot
            """, poke_id=poke_id, types=types)
            
        if abilities:
            tx.run("""
            MATCH (p:Pokemon {id: $poke_id})
            UNWIND $abilities AS ab_data
            MATCH (a:Ability {name: ab_data.name})
            MERGE (p)-[r:HAS_ABILITY]->(a)
            SET r.is_hidden = ab_data.is_hidden, r.slot = ab_data.slot
            """, poke_id=poke_id, abilities=abilities)

        if moves:
            tx.run("""
            MATCH (p:Pokemon {id: $poke_id})
            UNWIND $moves AS move_data
            MATCH (m:Move {name: move_data.name})
            MERGE (p)-[r:CAN_LEARN]->(m)
            SET r.versions = move_data.versions,
                r.methods = move_data.methods,
                r.levels = move_data.levels
            """, poke_id=poke_id, moves=moves)

    @staticmethod
    def _cypher_create_move_relations(tx, move_id, type_name):
        tx.run("""
        MATCH (m:Move {id: $move_id})
        MATCH (t:Type {name: $type_name})
        MERGE (m)-[:HAS_TYPE]->(t)
        """, move_id=move_id, type_name=type_name)


if __name__ == "__main__":
    builder = PokemonTopologyBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        print("==================================================")
        print(" Knowledge Graph Phase 2: Resumable Topology Sync ")
        print("==================================================")
        
        builder.build_move_relations()
        builder.build_pokemon_relations()
        
        print("\n🎉 Topology synchronization check completed!")
        
    finally:
        builder.close()