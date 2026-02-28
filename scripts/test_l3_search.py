import os
import sys
import json

# Path for secure utility and vstore
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.vector_store import VectorStore, MockEncoder

def test_l3_search(query: str):
    print(f"--- L3 SEARCH START: '{query}' ---")
    vs = VectorStore()
    encoder = MockEncoder()
    
    # 1. Get scope IDs from database (active scopes)
    vs.cur.execute("SELECT scope_id FROM scopes WHERE owner_id = 'wxu';")
    scope_ids = [row[0] for row in vs.cur.fetchall()]
    
    if not scope_ids:
        print("No active scopes found for search.")
        vs.close()
        return

    # 2. Encode search query
    query_vec = encoder.encode(query).tolist()
    
    # 3. Perform semantic L3 lookup
    results = vs.search_l3(scope_ids, query_vec, limit=5)
    
    if not results:
        print("No matches found in L3.")
    else:
        for sid, rid, text, metadata, sim in results:
            print(f"[Match - {sim:.4f}] {text}")
            print(f"  Record ID: {rid}")
            print(f"  Metadta: {metadata}")
            print("---")

    print("--- L3 SEARCH COMPLETE ---")
    vs.close()

if __name__ == "__main__":
    test_l3_search("truthfulness directive and versions")
    test_l3_search("redis protocol error fix")
