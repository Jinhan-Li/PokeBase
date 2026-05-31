import os
import json
import time
import requests

# ==========================================
# Configuration & Constants
# ==========================================
BASE_URL = "https://pokeapi.co/api/v2"
CACHE_BASE_DIR = "./cache"

# Define the targets and their expected max IDs
TARGETS = {
    "pokemon": 1025,
    "type": 18,
    "move": 919,
    "ability": 307,
    "evolution-chain": 550,
    "evolution-trigger": 20
}

def setup_directories():
    """
    Create the necessary directory structure for caching.
    E.g., ./cache/pokemon/, ./cache/type/
    """
    if not os.path.exists(CACHE_BASE_DIR):
        os.makedirs(CACHE_BASE_DIR)
        
    for endpoint in TARGETS.keys():
        dir_path = os.path.join(CACHE_BASE_DIR, endpoint)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"[*] Created directory: {dir_path}")

def fetch_and_cache(endpoint, max_id):
    """
    Fetches data from PokeAPI and saves it locally.
    Skips if the file already exists (Resumable feature).
    """
    dir_path = os.path.join(CACHE_BASE_DIR, endpoint)
    print(f"\n[+] Starting to cache {endpoint.capitalize()} (Target: {max_id} files)...")
    
    success_count = 0
    skip_count = 0
    error_count = 0

    for item_id in range(1, max_id + 1):
        file_path = os.path.join(dir_path, f"{item_id}.json")
        
        # 1. Skip if already cached (Idempotency)
        if os.path.exists(file_path):
            skip_count += 1
            continue
            
        # 2. Fetch from API
        url = f"{BASE_URL}/{endpoint}/{item_id}"
        try:
            # Added timeout to prevent hanging forever
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 3. Save to local disk
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    
                success_count += 1
                if item_id % 50 == 0:
                    print(f"    -> Downloaded {endpoint} ID: {item_id}")
            else:
                print(f"[-] Error: Got status code {response.status_code} for URL: {url}")
                error_count += 1
                
        except Exception as e:
            print(f"[-] Request failed for {url}. Error: {e}")
            error_count += 1
            
        # 4. Politeness delay to avoid rate-limiting by PokeAPI
        time.sleep(0.05) 

    # Summary report
    print(f"[*] {endpoint.capitalize()} Cache Summary: ")
    print(f"    - Newly Downloaded: {success_count}")
    print(f"    - Skipped (Already cached): {skip_count}")
    print(f"    - Errors: {error_count}")

if __name__ == "__main__":
    print("==============================================")
    print("  Knowledge Graph Phase 0: Local Data Cacher  ")
    print("==============================================")
    
    # Initialize folders
    setup_directories()
    
    # Execute caching for each target
    for endpoint, max_id in TARGETS.items():
        fetch_and_cache(endpoint, max_id)
        
    print("\n🎉 Phase 0 completed! All raw data is now safely cached on your local drive.")