import pandas as pd
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from rerank import infer_intent, rerank_results

# Load FAISS + metadata
index = faiss.read_index("shl_faiss.index")
with open("metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

def recommend(query, top_k=10):
    q_emb = model.encode([query]).astype("float32")
    _, I = index.search(q_emb, top_k)

    results = []
    for idx in I[0]:
        results.append({
            "assessment_name": metadata[idx]["assessment_name"],
            "url": metadata[idx]["url"],
            "test_type": metadata[idx]["test_type"]
        })

    intent = infer_intent(query)
    return rerank_results(results, intent, top_k)

# Load TEST queries (from same Excel / CSV)
df = pd.read_csv("test.csv")   # <-- test part of Gen_AI Dataset

rows = []

for _, row in df.iterrows():
    query = row["Query"]
    recs = recommend(query)

    for r in recs:
        rows.append({
            "Query": query,
            "Assessment_url": r["url"]
        })

submission = pd.DataFrame(rows)
submission.to_csv("final_submission.csv", index=False)

print("✅ final_submission.csv generated")
