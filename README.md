# 🎵 DefTunes: Data Engineering & AI Discoverability Capstone

[![Static RAG Demo](https://img.shields.io/badge/Live_Demo-DefTunes_AI-blueviolet?style=for-the-badge&logo=google-gemini)](https://chugh-gourav.github.io/deftunes_data_engineering_rag_capstone/)
[![ODCS v3.1](https://img.shields.io/badge/Data_Contract-ODCS_v3.1-orange?style=for-the-badge)](odcs_contracts/landing_datacontract.yaml)

---

## 📖 The Story: Helping Teams Find Data Faster

Every data-driven organization faces a silent bottleneck. For the **Business Analytics and Data Science communities**, getting quick access to technical metadata is the difference between a same-day business decision and a week-long research ticket.

When a Data Scientist or BA has to manually hunt for column definitions, quality rules, or SLAs across different contracts and files, it slows down the entire business.

**DefTunes AI** is a RAG assistant designed to solve this. It turns technical documentation into a conversation, delivering sub-2s answers to the people who need them most.

---

## 🏗️ How It Works

### Architecture Overview
A unified view of the contract-governed data pipeline and the AI-powered discovery engine.

```mermaid
flowchart TD
    subgraph "Phase 1: Governed Data Pipeline (Offline)"
        direction LR
        A["iTunes/User APIs"] --> B["generate_data.py"]
        B --> C[("GCS Data Lake")]
        C --> D{"ODCS Validation"}
        D -- "Pass" --> E[("BQ Landing")]
        E --> F["dbt Modeling"]
        F --> G{"ODCS Validation"}
        G -- "Pass" --> H[("BQ Serving")]
    end

    subgraph "Phase 2: AI Discovery Engine (Online)"
        direction TB
        I["ODCS Contracts + dbt Schemas"] --> J["Gemini Embeddings"]
        J --> K[("ChromaDB Index")]
        
        L["User Question"] --> M["Semantic Search"]
        K --> M
        M --> N["Augmented Prompt"]
        N --> O["Gemini 2.0 Flash"]
        O -- "Grounded Answer" --> P["Product Metadata"]
    end

    H -.-> I
```

### Data Lifecycle
1. **Ingest:** We pull raw music catalog and user interaction data from external APIs into our GCS landing zone.
2. **Transform:** Raw data is validated against ODCS contracts and modeled into clean dimensional tables using dbt.
3. **Index:** Technical metadata from contracts and schemas is embedded using Gemini and stored in a vector database.
4. **Serve:** The Streamlit assistant retrieves relevant context and answers natural language questions in real-time.

---

## 📈 Unit Economics (Illustrative Model)
*Illustrative model — assumptions listed above. Production validation via A/B test measuring time-to-answer vs. manual baseline.*

### Key Assumptions
- **London Market Rate:** £65 / hour (Mid-Senior Data Engineer fully-loaded cost).
- **Manual Task Time:** 15 minutes of searching and context switching.

### Cost Comparison (Per Task)

| Scenario | AI API Cost | Human Verification | Total Task Cost | Potential Gain |
| :--- | :--- | :--- | :--- | :--- |
| **Manual Search** | £0.00 | 15 mins (£16.25) | **£16.25** | - |
| **Basic RAG (Current)** | $0.0003 | 5 mins (£5.41) | **~£5.42** | **3x Saving** |
| **Advanced AI (Future)** | $0.05 | 1 min (£1.08) | **~£1.14** | **14x Saving** |

---

## 🧠 Scaling the System: 22 vs. 22,000 Chunks

As the knowledge base grows 1,000x, we shift our strategy to maintain accuracy.

**1. Stable Costs**
RAG decouples data size from AI cost. Even at 22,000 chunks, we only retrieve the top **k=5** matches, so the AI token cost stays fixed at **~$0.0003/query**.

**2. Managing Noise**
To keep accuracy high at a larger scale, we would move toward:
- **Agentic Workflows:** Using the AI to "judge" its own answers before showing them to humans.
- **GraphRAG:** Linking data entities (like Project → Owner → Contract) into a "map" so the search follows logical relationships instead of just keywords.

---

## 🔗 Reference Case Studies & Links
Industry leaders are using similar strategies to handle internal documentation and compliance:

*   **[KPMG Adoption Case Study](https://www.techuk.org/resource/ai-adoption-case-study-kpmg-s-ava-gen-ai-tool-creates-useable-outputs-improves-efficiences-and-reduces-risk.html):** How AI tools improve efficiencies and reduce risk in professional services.
*   **[Nasdaq / Progress RAG Platform](https://www.nasdaq.com/press-release/progress-software-unveils-breakthrough-saas-rag-platform-designed-make-trustworthy):** Breakthrough in building trustworthy AI for high-compliance environments.
*   **[Autodesk Assistant Platform](https://aws.amazon.com/blogs/machine-learning/autodesk-assistant-building-an-agentic-platform-on-amazon-bedrock/):** Moving from basic search to an assistant that navigates complex technical data.

---

## 🚀 Future Ideas
1. **Automated Verification:** Using a "judge" model to automatically verify AI answers. *Prioritized first as it directly reduces human verification cost, the dominant driver in our unit economics model.*
2. **Broader Data Silos:** Linking this to Jira tickets and Slack history to capture "tribal knowledge" that isn't in the official contracts.
3. **Actionable AI:** Having the assistant suggest schema changes or draft new Data Contracts based on user questions.

---

## 🎯 Production Success Metrics
* **Retrieval accuracy:** Measured via MRR or NDCG@5 (Target: 95%+).
* **Answer latency:** p95 service response time (Target: <2s).
* **Cost efficiency:** Total API cost per query per month (Target: <$0.001).

---

## 📂 Project Structure
```
deftunes_capstone/
├── odcs_contracts/      # ODCS v3.1 Data Contracts  ← Source of Truth
├── rag_app/             # Streamlit Chat UI + ChromaDB (Skyscanner Theme)
└── dbt_modeling/        # Core Business Logic (Fact / Dim / Views)
```

## 👤 Author: Gourav Chugh
**AI/Data Product Manager**  
[GitHub Portfolio](https://github.com/Chugh-Gourav)

---
*Built for the AI Product Management Capstone — DefTunes Project.*
