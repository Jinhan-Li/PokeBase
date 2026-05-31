import requests
import time
from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class PokemonNodeBuilder:
    def __init__(self, uri, user, password):
        """
        Initialize the Neo4j driver to connect to AuraDB.
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.base_url = "https://pokeapi.co/api/v2"

    def close(self):
        """
        Close the database connection.
        """
        self.driver.close()

    def fetch_api_data(self, endpoint):
        """
        Helper method to fetch JSON data from PokeAPI with basic error handling.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[-] Failed to fetch {url} (Status Code: {response.status_code})")
                return None
        except Exception as e:
            print(f"[-] Request error for {url}: {e}")
            return None

    def get_existing_ids(self, label_name):
        """
        Query the database to get a set of all existing IDs for a specific Label.
        Using a Set provides O(1) lookup time for the skip logic.
        """
        # Note: Cypher doesn't allow parameterizing node labels directly, 
        # so we use Python string formatting for the label name.
        query = f"MATCH (n:{label_name}) RETURN n.id AS id"
        with self.driver.session() as session:
            result = session.run(query)
            # Comprehend the results into a Python set, ignoring any potential None values
            existing_ids = {record["id"] for record in result if record["id"] is not None}
        return existing_ids

    # ==========================================
    # Node Creation Methods (Transactions)
    # ==========================================

    @staticmethod
    def _create_pokemon_node(tx, data):
        query = """
        MERGE (p:Pokemon {id: $id})
        SET p.name = $name,
            p.height = $height,
            p.weight = $weight,
            p.base_experience = $base_experience
        """
        tx.run(query, 
               id=data.get('id'), 
               name=data.get('name'), 
               height=data.get('height'), 
               weight=data.get('weight'), 
               base_experience=data.get('base_experience'))

    @staticmethod
    def _create_type_node(tx, data):
        query = """
        MERGE (t:Type {id: $id})
        SET t.name = $name
        """
        tx.run(query, id=data.get('id'), name=data.get('name'))

    @staticmethod
    def _create_ability_node(tx, data):
        query = """
        MERGE (a:Ability {id: $id})
        SET a.name = $name
        """
        tx.run(query, id=data.get('id'), name=data.get('name'))

    @staticmethod
    def _create_move_node(tx, data):
        query = """
        MERGE (m:Move {id: $id})
        SET m.name = $name,
            m.accuracy = $accuracy,
            m.priority = $priority,
            m.pp = $pp,
            m.power = $power
        """
        tx.run(query, 
               id=data.get('id'), 
               name=data.get('name'),
               accuracy=data.get('accuracy'),
               priority=data.get('priority'),
               pp=data.get('pp'),
               power=data.get('power'))

    # ==========================================
    # Main Execution Pipelines (With Skip Logic)
    # ==========================================

    def load_all_types(self, max_id=18):
        existing_ids = self.get_existing_ids("Type")
        print(f"\n[+] Starting to load Types (Existing: {len(existing_ids)})...")
        
        with self.driver.session() as session:
            for i in range(1, max_id + 1):
                if i in existing_ids:
                    # Skip if already exists
                    continue
                
                data = self.fetch_api_data(f"type/{i}")
                if data:
                    session.execute_write(self._create_type_node, data)
                    print(f"    [INSERTED] Type: {data['name']} (ID: {i})")
                time.sleep(0.05)

    def load_all_abilities(self, max_id=307):
        existing_ids = self.get_existing_ids("Ability")
        print(f"\n[+] Starting to load Abilities (Existing: {len(existing_ids)})...")
        
        with self.driver.session() as session:
            for i in range(1, max_id + 1):
                if i in existing_ids:
                    continue
                
                data = self.fetch_api_data(f"ability/{i}")
                if data:
                    session.execute_write(self._create_ability_node, data)
                    print(f"    [INSERTED] Ability (ID: {i})")
                time.sleep(0.05)
        print("    Finished loading Abilities.")

    def load_moves(self, max_id=165):
        existing_ids = self.get_existing_ids("Move")
        print(f"\n[+] Starting to load Moves (Existing: {len(existing_ids)})...")
        
        with self.driver.session() as session:
            for i in range(1, max_id + 1):
                if i in existing_ids:
                    continue
                
                data = self.fetch_api_data(f"move/{i}")
                if data:
                    session.execute_write(self._create_move_node, data)
                    print(f"    [INSERTED] Move (ID: {i})")
                time.sleep(0.05)
        print("    Finished loading Moves.")

    def load_pokemon(self, start_id=1, end_id=151):
        existing_ids = self.get_existing_ids("Pokemon")
        print(f"\n[+] Starting to load Pokemon (Existing: {len(existing_ids)})...")
        
        with self.driver.session() as session:
            for i in range(start_id, end_id + 1):
                if i in existing_ids:
                    continue
                
                data = self.fetch_api_data(f"pokemon/{i}")
                if data:
                    session.execute_write(self._create_pokemon_node, data)
                    print(f"    [INSERTED] Pokemon: {data['name']} (ID: {i})")
                time.sleep(0.1)
        print("    Finished loading Pokemon.")


if __name__ == "__main__":
    builder = PokemonNodeBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        print("==============================================")
        print("  Knowledge Graph Phase 1: Resumable Builder  ")
        print("==============================================")
        
        builder.load_all_types(max_id=18)
        builder.load_all_abilities(max_id=307)
        builder.load_moves(max_id=919) 
        builder.load_pokemon(start_id=1, end_id=1025)
        
        print("\n🎉 Phase 1 validation and completion successful!")
        
    finally:
        builder.close()