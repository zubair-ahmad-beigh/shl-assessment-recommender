import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# Load FAISS index
index = faiss.read_index("shl_faiss.index")

# Load metadata
with open("metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Test query
query = "Java developer with good communication skills"

query_embedding = model.encode([query]).astype("float32")

# Search top 10
D, I = index.search(query_embedding, 10)

print("\nTop Recommendations:\n")
for rank, idx in enumerate(I[0], start=1):
    item = metadata[idx]
    print(f"{rank}. {item['assessment_name']}")
    print(f"   Type: {item['test_type']}")
    print(f"   URL: {item['url']}\n")
