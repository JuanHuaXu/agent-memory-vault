import psycopg2
from pgvector.psycopg2 import register_vector
import os
import sys
import numpy as np

# Path for secure utility
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.secret_utility import get_secret
from core.db import get_db_connection

class VectorStore:
    def __init__(self):
        self.conn = get_db_connection()
        # Skipped register_vector as it can hang in some environments
        self.cur = self.conn.cursor()

    def add_snippet(self, record_id, scope_id, text, metadata, embedding):
        """Inserts a new L3 snippet with its vector embedding."""
        try:
            # Manually cast to vector string for Postgres
            emb_str = "[" + ",".join(map(str, embedding)) + "]"
            self.cur.execute("""
                INSERT INTO l3_snippets (record_id, scope_id, text, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s::vector)
            """, (record_id, scope_id, text, metadata, emb_str))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding snippet to L3: {e}")
            self.conn.rollback()
            return False

    def search_l3(self, scope_ids, query_embedding, limit=10):
        """Performs a semantic search across multiple scopes."""
        try:
            # Using <=> for cosine distance in pgvector
            emb_str = "[" + ",".join(map(str, query_embedding)) + "]"
            self.cur.execute("""
                SELECT snippet_id, record_id, text, metadata, 1 - (embedding <=> %s::vector) AS cosine_similarity
                FROM l3_snippets
                WHERE scope_id = ANY(%s::uuid[])
                ORDER BY cosine_similarity DESC
                LIMIT %s
            """, (emb_str, scope_ids, limit))
            return self.cur.fetchall()
        except Exception as e:
            print(f"L3 Search Error: {e}")
            return []

    def close(self):
        self.cur.close()
        self.conn.close()

# Mock Embedding Engine for phase 1
class MockEncoder:
    def __init__(self, dimension=1536):
        self.dimension = dimension

    def encode(self, text):
        """Generates a stable mock embedding for a given text."""
        # Use simple hash-based seed for reproducibility in dev
        import hashlib
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        random_gen = np.random.RandomState(seed)
        vec = random_gen.randn(self.dimension)
        return vec / np.linalg.norm(vec)

if __name__ == "__main__":
    # Smoke test
    print("Initializing Vector Store...")
    vs = VectorStore()
    encoder = MockEncoder()
    print("Vector Store Ready.")
    vs.close()
