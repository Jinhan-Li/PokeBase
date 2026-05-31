import os
import json
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

CACHE_BASE_DIR = "./cache"
EVO_DIR = os.path.join(CACHE_BASE_DIR, "evolution-chain")

class EvolutionTopologyBuilder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def load_json(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ==========================================
    # Parsing Logic for Evolution Chains
    # ==========================================

    def _extract_evolutions(self, node, results):
        """
        Recursively extract all [from_species, to_species, details] relationships
        from the deeply nested PokeAPI evolution chain structure.
        """
        base_name = node['species']['name']
        
        for evolution in node['evolves_to']:
            evolved_name = evolution['species']['name']
            
            # Record non-null evolution condition details
            details_list = []
            min_level = None
            item = None
            
            for det in evolution.get('evolution_details', []):
                cleaned_det = {}
                for k, v in det.items():
                    if v is not None and v != "":
                        # If the detail is an object (like item, trigger, etc.), extract its name
                        if isinstance(v, dict) and 'name' in v:
                            cleaned_det[k] = v['name']
                        elif not isinstance(v, dict):
                            cleaned_det[k] = v
                if cleaned_det:
                    details_list.append(cleaned_det)
                    
                # Extract explicit semantic properties for clean Cypher querying
                if min_level is None and cleaned_det.get('min_level'):
                    min_level = cleaned_det['min_level']
                if item is None and cleaned_det.get('item'):
                    item = cleaned_det['item']
                    
            # Convert to JSON string so Neo4j can store the dynamic structure property
            details_str = json.dumps(details_list, ensure_ascii=False)
            
            params = {
                'details': details_str,
                'min_level': min_level,
                'item': item
            }
            results.append((base_name, evolved_name, params))
            
            # Recursive traversal for multi-stage evolutions (e.g. Charmander -> Charmeleon -> Charizard)
            self._extract_evolutions(evolution, results)

    # ==========================================
    # Cypher Query Builder
    # ==========================================

    @staticmethod
    def _cypher_create_evolution_relations(tx, relationships):
        """
        relationships: List of Tuple (from_name, to_name, dict_of_params)
        """
        query = """
        UNWIND $relations AS rel
        MATCH (from:Pokemon {name: rel.from_name})
        MATCH (to:Pokemon {name: rel.to_name})
        
        MERGE (from)-[r1:EVOLVES_TO]->(to)
        SET r1.details = rel.params.details,
            r1.min_level = rel.params.min_level,
            r1.item = rel.params.item
        
        MERGE (to)-[r2:EVOLVES_FROM]->(from)
        SET r2.details = rel.params.details,
            r2.min_level = rel.params.min_level,
            r2.item = rel.params.item
        """
        
        # Prepare the payload for batch execution
        payload = []
        for from_name, to_name, params in relationships:
            payload.append({
                "from_name": from_name,
                "to_name": to_name,
                "params": params
            })
            
        if payload:
            tx.run(query, relations=payload)

    # ==========================================
    # Main Execution Pipeline
    # ==========================================

    def build_evolution_relations(self):
        print("\n[*] Building Evolution Relations...")
        
        if not os.path.exists(EVO_DIR):
            print(f"[-] Directory {EVO_DIR} does not exist. Please run Phase 0 cacher first.")
            return

        files = [f for f in os.listdir(EVO_DIR) if f.endswith('.json')]
        # Sort numerically
        files.sort(key=lambda x: int(x.split('.')[0]))
        
        success_count = 0

        for filename in files:
            evo_id = int(filename.split('.')[0])
            filepath = os.path.join(EVO_DIR, filename)
            
            try:
                data = self.load_json(filepath)
                if not data or 'chain' not in data:
                    continue
                
                # Parse all evolutionary links in this family tree
                relationships = []
                self._extract_evolutions(data['chain'], relationships)
                
                if relationships:
                    with self.driver.session() as session:
                        session.execute_write(self._cypher_create_evolution_relations, relationships)
                    success_count += 1
                    
                if evo_id % 50 == 0:
                    print(f"    [+] Successfully processed evolution chain ID: {evo_id}")
                    
            except Exception as e:
                print(f"    [-] ERROR processing Evolution ID {evo_id}: {e}")

        print(f"[*] Evolution relations phase completed. Inserted {success_count} chains.")

if __name__ == "__main__":
    print("==================================================")
    print("  Knowledge Graph Phase 3: Building Evolutions  ")
    print("==================================================")
    
    builder = EvolutionTopologyBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        builder.build_evolution_relations()
    finally:
        builder.close()