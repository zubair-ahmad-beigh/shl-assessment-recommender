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

# Build keyword map from scraped assessments
assessment_texts = [
    (m["url"], f"{m['assessment_name']} {m.get('category','')}".lower())
    for m in metadata
]

def recommend(query, top_k=10):
    q_emb = model.encode([query]).astype("float32")
    _, I = index.search(q_emb, top_k)

    results = []
    for idx in I[0]:
        results.append({
            "url": metadata[idx]["url"],
            "assessment_name": metadata[idx]["assessment_name"],
            "test_type": metadata[idx]["test_type"]
        })

    intent = infer_intent(query)
    return rerank_results(results, intent, top_k)

# Load train queries only (ignore URLs)
df = pd.read_csv("train.csv")

# Surrogate recall: keyword overlap
def surrogate_recall(query, recommendations):
    q_words = set(query.lower().split())
    hits = 0
    for r in recommendations:
        a_words = set(r["assessment_name"].lower().split())
        if len(q_words & a_words) > 0:
            hits += 1
    return hits / len(recommendations) if recommendations else 0

scores = []

for _, row in df.iterrows():
    query = row["Query"]
    recs = recommend(query)
    score = surrogate_recall(query, recs)
    scores.append(score)

print("✅ Surrogate Evaluation Score:", round(sum(scores) / len(scores), 3))
