import os
import json
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

# Define the local cache directory for types
CACHE_BASE_DIR = "./cache"
TYPE_DIR = os.path.join(CACHE_BASE_DIR, "type")

class PokemonTypeRelationBuilder:
    def __init__(self, uri, user, password):
        """Initialize the Neo4j driver."""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Close the database connection."""
        self.driver.close()

    def load_json(self, filepath):
        """Helper to load a single JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ==========================================
    # Parsing and Building Logic
    # ==========================================

    def build_type_damage_relations(self):
        """
        Parses type JSONs and builds[:DAMAGE_TO {multiplier: X}] relationships.
        We only process the '*_damage_to' fields to avoid redundant bidirectional parsing.
        """
        print("\n[*] Building Type Damage Relations (Type -> DAMAGE_TO -> Type)...")
        
        # Ensure directory exists and get all JSON files
        if not os.path.exists(TYPE_DIR):
            print(f"[-] Error: Cache directory {TYPE_DIR} not found. Run Phase 0 first.")
            return

        files =[f for f in os.listdir(TYPE_DIR) if f.endswith('.json')]
        
        for filename in files:
            data = self.load_json(os.path.join(TYPE_DIR, filename))
            source_type_name = data['name']
            damage_relations = data['damage_relations']
            
            # Extract target type names for each multiplier category
            double_to = [t['name'] for t in damage_relations.get('double_damage_to',[])]
            half_to = [t['name'] for t in damage_relations.get('half_damage_to', [])]
            no_to = [t['name'] for t in damage_relations.get('no_damage_to',[])]
            
            # Execute transactions
            with self.driver.session() as session:
                if double_to:
                    session.execute_write(self._cypher_create_damage_edge, source_type_name, double_to, 2.0)
                if half_to:
                    session.execute_write(self._cypher_create_damage_edge, source_type_name, half_to, 0.5)
                if no_to:
                    session.execute_write(self._cypher_create_damage_edge, source_type_name, no_to, 0.0)
                    
            print(f"    [+] Processed damage relations for Type: {source_type_name}")
            
        print("\n[*] Type Damage Relations established successfully!")

    # ==========================================
    # Cypher Transactions
    # ==========================================

    @staticmethod
    def _cypher_create_damage_edge(tx, source_type, target_types, multiplier):
        """
        Cypher execution to MERGE[:DAMAGE_TO] edge and SET the multiplier.
        Uses UNWIND for efficient batch insertion of targets.
        """
        tx.run("""
        MATCH (source:Type {name: $source_type})
        UNWIND $target_types AS target_name
        MATCH (target:Type {name: target_name})
        
        // Use MERGE to ensure idempotency (can be run multiple times safely)
        MERGE (source)-[r:DAMAGE_TO]->(target)
        SET r.multiplier = $multiplier
        """, source_type=source_type, target_types=target_types, multiplier=multiplier)


if __name__ == "__main__":
    builder = PokemonTypeRelationBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        print("=====================================================")
        print(" Knowledge Graph Phase 2.5: Type Effectiveness Sync  ")
        print("=====================================================")
        
        builder.build_type_damage_relations()
        
        print("\n🎉 Phase 2.5 completed!")
        
    finally:
        builder.close()