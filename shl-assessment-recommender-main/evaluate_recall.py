import pandas as pd
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from rerank import infer_intent, rerank_results

# ===============================
# LOAD FAISS + METADATA
# ===============================
index = faiss.read_index("shl_faiss.index")

with open("metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")

# Build set of URLs available in our scraped dataset
available_urls = set([m["url"] for m in metadata])


# ===============================
# RECOMMEND FUNCTION
# ===============================
def recommend(query, top_k=10):
    # Encode query
    q_emb = model.encode([query]).astype("float32")

    # FAISS search
    _, I = index.search(q_emb, top_k)

    # Collect FAISS results
    faiss_results = []
    for idx in I[0]:
        faiss_results.append({
            "assessment_name": metadata[idx]["assessment_name"],
            "url": metadata[idx]["url"],
            "test_type": metadata[idx]["test_type"]
        })

    # Intent-aware re-ranking
    intent = infer_intent(query)
    final_results = rerank_results(faiss_results, intent, top_k)

    return [r["url"] for r in final_results]


# ===============================
# RECALL@10 FUNCTION
# ===============================
def recall_at_10(true_urls, predicted_urls):
    true_set = set(true_urls)
    pred_set = set(predicted_urls)
    hits = len(true_set & pred_set)
    return hits / len(true_set) if true_set else 0


# ===============================
# LOAD TRAIN DATA
# ===============================
df = pd.read_csv("train.csv")

# ===============================
# FILTER TRAIN QUERIES
# ===============================
filtered_queries = []

for _, row in df.iterrows():
    query = row["Query"]
    true_urls = row["Assessment_url"].split("|")

    # Keep only URLs that exist in our scraped dataset
    true_urls = [u for u in true_urls if u in available_urls]

    if true_urls:
        filtered_queries.append((query, true_urls))

print(f"✅ Evaluating on {len(filtered_queries)} valid queries "
      f"(with ground-truth URLs present in scraped data)")

# ===============================
# RUN EVALUATION
# ===============================
scores = []

for query, true_urls in filtered_queries:
    predicted_urls = recommend(query)
    score = recall_at_10(true_urls, predicted_urls)
    scores.append(score)

if scores:
    mean_recall = round(sum(scores) / len(scores), 3)
    print(f"🎯 Mean Recall@10: {mean_recall}")
else:
    print("⚠️ No overlapping ground-truth URLs found. Recall cannot be computed.")
