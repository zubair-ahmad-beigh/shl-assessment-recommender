import pandas as pd
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer

# Load data
df = pd.read_csv("shl_assessments.csv")

# Combine text fields
def build_text(row):
    return f"{row['assessment_name']} {row.get('description','')} {row.get('category','')}"

texts = df.apply(build_text, axis=1).tolist()

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Generating embeddings...")
embeddings = model.encode(texts, show_progress_bar=True)

# Convert to float32 for FAISS
embeddings = np.array(embeddings).astype("float32")

# Create FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

print(f"Total embeddings indexed: {index.ntotal}")

# Save index
faiss.write_index(index, "shl_faiss.index")

# Save metadata
metadata = df[["assessment_name", "url", "test_type", "category"]].to_dict(orient="records")
with open("metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)

print("FAISS index and metadata saved successfully.")
