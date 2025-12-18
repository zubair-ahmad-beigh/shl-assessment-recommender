# SHL Assessment Recommendation System

An intelligent system that recommends SHL Individual Test Solutions based on natural language queries, job descriptions, or job description URLs.

## Overview

This system:
1. Scrapes SHL's product catalog to extract Individual Test Solutions
2. Builds embeddings using SentenceTransformers
3. Uses FAISS for efficient similarity search
4. Leverages LLM (Gemini) for intent extraction and query understanding
5. Provides balanced recommendations (Knowledge & Skills + Personality & Behavior)

## Project Structure

```
.
├── scraper.py              # SHL catalog scraper
├── data/                   # Scraped data storage
├── embeddings.py           # Embedding generation and FAISS indexing
├── recommender.py          # Recommendation logic with LLM
├── api.py                  # FastAPI backend
├── evaluation.py           # Recall@10 evaluation
├── streamlit_app.py        # Streamlit frontend
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Scrape SHL Catalog

Run the scraper to extract Individual Test Solutions:

```bash
python scraper.py
```

This will generate:
- `shl_assessments.csv`
- `shl_assessments.json`
- `debug_catalog_page.html` (for debugging)

**Expected output:** At least 377 Individual Test Solutions

## Usage

### Running the FastAPI Backend

```bash
uvicorn api:app --reload
```

API will be available at `http://localhost:8000`

### Running the Streamlit Frontend

```bash
streamlit run streamlit_app.py
```

Frontend will be available at `http://localhost:8501`

## API Endpoints

### GET /health

Returns API status.

**Response:**
```json
{
  "status": "healthy",
  "assessments_loaded": 377
}
```

### POST /recommend

Accepts a query, job description, or job description URL and returns 5-10 relevant assessments.

**Request:**
```json
{
  "query": "Software engineer position requiring problem-solving and coding skills",
  "job_description": null,
  "job_description_url": null
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "assessment_name": "Verbal Reasoning",
      "assessment_url": "https://www.shl.com/...",
      "test_type": "K",
      "similarity_score": 0.85
    },
    ...
  ]
}
```

## Evaluation

Run evaluation on the training dataset:

```bash
python evaluation.py
```

This will:
1. Compute Recall@10 on the training set
2. Show initial and improved metrics
3. Generate predictions for the test set in `test_predictions.csv`

## Data Format

### Scraped Assessments (CSV/JSON)

- `assessment_name`: Name of the assessment
- `description`: Description text
- `test_type`: K (Knowledge/Skills) or P (Personality/Behavior)
- `category`: Category classification
- `url`: Full URL to the assessment page

### Test Predictions (CSV)

- `query`: Original query text
- `assessment_url`: Recommended assessment URL

## Development Workflow

1. ✅ Scrape SHL catalog
2. ⏳ Build embeddings and FAISS index
3. ⏳ Implement recommendation logic
4. ⏳ Build FastAPI backend
5. ⏳ Implement evaluation
6. ⏳ Generate test predictions
7. ⏳ Build Streamlit frontend

## Notes

- The scraper uses multiple strategies to extract assessments from the catalog
- Test types (K/P) are automatically detected from text patterns
- Pre-packaged Job Solutions are explicitly excluded
- The system ensures balanced recommendations between K and P test types





