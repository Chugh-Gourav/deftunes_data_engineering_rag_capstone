# 🎵 DefTunes: AI Discoverability and Data Pipeline

An end-to-end **GCP data pipeline** and **AI-powered data discoverability** application for a simulated music streaming platform. Built to demonstrate how a **Data/AI Product Manager** can design, build, and document data products using modern cloud-native tools.

> **Live Demo:** [Try the AI Discoverability App →](https://chugh-gourav.github.io/deftunes_data_engineering_rag_capstone/)  
> Enter your Gemini API key and ask questions about the DefTunes data ecosystem.

---

## 🏗️ Architecture

### Data Pipeline
```mermaid
flowchart LR
    subgraph "Data Sources"
        A[🎵 iTunes API<br/>1,000 songs]
        B[👤 Random User API<br/>5,000 users]
    end
    
    subgraph "Data Generation"
        C[generate_data.py<br/>NDJSON output]
    end
    
    subgraph "Google Cloud Platform"
        D[(GCS Bucket<br/>landing_zone/)]
        E[(BigQuery<br/>deftunes_landing_zone)]
        F[(BigQuery<br/>deftunes_transform_db)]
    end
    
    subgraph "Transformation"
        G[dbt<br/>5 tables + 2 views]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    E --> G
    G --> F
```

### RAG Discoverability App
```mermaid
flowchart LR
    subgraph "Knowledge Base"
        A[📄 ODCS Contracts<br/>landing + serving]
        B[📊 dbt Schemas<br/>7 models]
    end
    
    subgraph "Embedding Layer"
        C[Gemini Embedding 001<br/>Text → Vectors]
        D[(ChromaDB<br/>Vector Store<br/>22 chunks)]
    end
    
    subgraph "Retrieval + Generation"
        E[Semantic Search<br/>Top-k=5 retrieval]
        F[Gemini 2.0 Flash<br/>Grounded answer]
    end
    
    subgraph "User Interface"
        G[💬 Streamlit Chat UI<br/>localhost:8501]
    end
    
    A --> C
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
```

---

## 📊 Data Model

| Layer | Table | Rows | Description |
|-------|-------|------|-------------|
| **Landing** | `raw_users` | 5,000 | User profiles with geography |
| **Landing** | `raw_songs` | 1,000 | Song catalog from iTunes API |
| **Landing** | `raw_sessions` | 100,000 | Listening events (30-day window) |
| **Landing** | `raw_user_feedback` | 50,000 | Likes, dislikes, skips, playlist adds |
| **Serving** | `fact_session` | 100,000 | Cleaned session facts |
| **Serving** | `fact_feedback` | 50,000 | Cleaned interaction facts |
| **Serving** | `dim_artists` | 552 | Deduplicated artist dimension |
| **Serving** | `dim_songs` | 1,000 | Song dimension with artist linkage |
| **Serving** | `dim_users` | 5,000 | User dimension with geography |
| **BI Views** | `interactions_per_artist_vw` | - | Likes/dislikes aggregated by artist |
| **BI Views** | `interactions_per_country_vw` | - | Interactions aggregated by country |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Cloud** | Google Cloud Platform (GCS, BigQuery) |
| **Orchestration** | Apache Airflow (Cloud Composer) |
| **Transformation** | dbt (dbt-bigquery adapter) |
| **Data Contracts** | ODCS v3.1.0 |
| **AI / LLM** | Google Gemini 2.0 Flash |
| **Embeddings** | Gemini Embedding 001 |
| **Vector Store** | ChromaDB (local Streamlit version) |
| **Frontend** | Static HTML/JS (GitHub Pages) |
| **Data Format** | NDJSON (Newline Delimited JSON) |

---

## 📁 Project Structure

```
deftunes_data_engineering_rag_capstone/
├── README.md
├── requirements.txt
│
├── data_generator/             # Phase 1: Data Generation
│   ├── generate_data.py        # Fetch songs (iTunes API) + simulate users/sessions/feedback
│   ├── load_to_bq.py           # Load NDJSON from GCS → BigQuery landing zone
│   └── test_spotify.py         # Spotify API evaluation (documented pivot)
│
├── dags/                       # Phase 2: Orchestration
│   └── gcp_deftunes_pipeline.py  # Airflow DAG for production ingestion
│
├── dbt_modeling/               # Phase 3: Transformation
│   ├── dbt_project.yml
│   └── models/
│       ├── serving_layer/      # Fact + dimension tables
│       └── bi_views/           # Aggregated interaction views
│
├── odcs_contracts/             # Phase 4: Data Contracts
│   ├── landing_datacontract.yaml
│   └── serving_datacontract.yaml
│
├── rag_app/                    # Phase 5A: RAG App (Streamlit + ChromaDB)
│   ├── app.py
│   ├── ingest.py
│   └── requirements.txt
│
└── docs/                       # Phase 5B: RAG App (GitHub Pages)
    └── index.html              # Static AI chat — no backend required
```

---

## 🚀 Quick Start

### 1. Generate Data
```bash
cd data_generator
pip install requests
python generate_data.py
```

### 2. Upload to GCS & Load to BigQuery
```bash
# Upload NDJSON files to GCS (requires gcloud auth)
gsutil cp *.json gs://ai-data-product-work-data-lake/landing_zone/

# Load into BigQuery
pip install google-cloud-bigquery
python load_to_bq.py
```

### 3. Run dbt Transformations
```bash
cd ../dbt_modeling
pip install dbt-bigquery
dbt run   # Build 7 models
dbt test  # Run 6 data quality tests
```

### 4. Launch RAG App (Local)
```bash
cd ../rag_app
pip install -r requirements.txt
export GOOGLE_API_KEY="your-gemini-api-key"
python ingest.py          # Build ChromaDB vector store
streamlit run app.py      # Launch at localhost:8501
```

### 5. Launch RAG App (GitHub Pages)
Simply open `docs/index.html` in a browser, or visit the [live demo](https://chugh-gourav.github.io/deftunes_data_engineering_rag_capstone/).

---

## 📋 Data Contracts (ODCS v3.1)

This project uses **Open Data Contract Standard** to formally define data ownership, schema, quality rules, and SLAs:

- **[Landing Contract](odcs_contracts/landing_datacontract.yaml)** — Defines raw data tables, field types, and freshness guarantees
- **[Serving Contract](odcs_contracts/serving_datacontract.yaml)** — Defines transformed models, BI views, and quality validation rules

## 📊 AI Product Economics: ROI & Unit Costs

As an AI PM, managing the **Unit Economics** of an LLM feature is as important as the accuracy. Our RAG implementation is optimized for the following profile:

### 1. The Token Budget (Per Query)
*   **Prompt (Input)**: ~1,900 tokens (System Instructions + 5 Retrieved Chunks).
*   **Completion (Output)**: ~200 tokens (Concise metadata-driven answer).
*   **Total**: ~2,100 tokens.

### 2. Unit Costs (Gemini 2.0 Flash)
*   **Input Cost**: $0.10 per 1 million tokens.
*   **Output Cost**: $0.40 per 1 million tokens.
*   **Cost per Query**: **$0.00027** (roughly 1/37th of a cent).
*   **Verified Benchmark**: A query for *"Likes by artist and country"* used **233 prompt tokens** and **248 output tokens** in our test environment.
*   **Scale Efficiency**: You can run **~3,700 queries for $1.00**.

### 3. The RAG vs. Long-Context Tradeoff
| Strategy | Tokens / Query | Cost / 1k Queries | Latency (Avg) |
| :--- | :--- | :--- | :--- |
| **Full Context (k=22)** | ~6,500 | $0.72 | 4.5s |
| **RAG Optimized (k=5)** | **~2,100** | **$0.27 (63% Saving)** | **1.8s (60% Faster)** |

### 4. Business ROI
*   **Efficiency**: A Data Engineer spends roughly **15-30 minutes** searching through YAML and SQL to answer a schema question. This AI delivers the same confidence in **<2 seconds**.
*   **Cost of Search**: $0.00027 (AI) vs. ~$25.00 (Human hourly rate adjusted for 30 mins).
*   **ROI**: **>90,000x** cost reduction for internal data discovery.

---

## 👤 Author

**Gourav Chugh**  
[GitHub](https://github.com/Chugh-Gourav) · AI Product Management
