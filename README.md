# 🎵 DefTunes: Data Engineering & AI Discoverability Capstone

[![Static RAG Demo](https://img.shields.io/badge/Live_Demo-DefTunes_AI-blueviolet?style=for-the-badge&logo=google-gemini)](https://chugh-gourav.github.io/deftunes_data_engineering_rag_capstone/)
[![ODCS v3.1](https://img.shields.io/badge/Data_Contract-ODCS_v3.1-orange?style=for-the-badge)](odcs_contracts/landing_datacontract.yaml)

---

## 📖 The Executive Summary: Solving the Knowledge Interruption Tax

Every data-driven organization faces a silent, compounding bottleneck. For the **Business Analytics and Data Science communities**, the frictionless access to technical metadata is the difference between a same-day strategic pivot and a week-long research ticket.

When a Data Scientist or BA has to manually hunt for column definitions, quality rules, or SLAs across ODCS contracts and dbt schemas, the cost isn't just the minutes lost—it's the **latency of the business decision.**

**DefTunes AI** is an Executive-grade Retrieval-Augmented Generation (RAG) assistant that bridges this gap. By turning static governance into a conversational interface, we enable 10x faster access to "The Truth," ensuring that high-stakes analytics are built on verified data foundations.

---

## 📈 Unit Economics: The "Trust Tax" & ROI

To build a board-ready business case, we must account for the **cost of verification**. While an AI query cost is near-zero, the economic cost of a senior engineer spending time verifying output (The "Trust Tax") must be factored in.

### London Market Assumptions
*   **Blended Rate (London):** £65 / hour (Mid-Senior Data Engineer fully-loaded cost).
*   **Manual Task Cost:** 15 minutes = **£16.25**.

### Comparative Economics (Task Completion Cost)

| Scenario | Raw AI Cost | Human Verification | Total Task Cost | ROI (vs Manual) |
| :--- | :--- | :--- | :--- | :--- |
| **Manual Search** | £0.00 | 15 mins (£16.25) | **£16.25** | - |
| **Basic RAG (Current)** | $0.0003 | 5 mins (£5.41) * | **~£5.42** | **3x Gain** |
| **Agentic RAG (Future)** | $0.05 | 1 min (£1.08) ** | **~£1.14** | **14x Gain** |

*\* Basic RAG requires higher manual verification due to "hallucination risk" in noisy environments.*  
*\*\* Agentic RAG uses a "judge" model to verify results before showing them to the user, slashing human review time.*

---

## 🧠 Strategic Scalability: 22 vs. 22,000 Chunks

As the knowledge base grows 1,000x, we shift from "Search" to "Reasoning."

### 1. Decoupled Cost
RAG naturally scales because we only ever retrieve the top **k=5** chunks. Even at 22,000 chunks, the LLM token cost remains fixed at **~$0.0003/query**.

### 2. Eliminating Noise with GraphRAG & Agents
In an enterprise context, simple vector search becomes risky. To maintain 99%+ accuracy at scale, the roadmap includes:
*   **GraphRAG:** Linking entities (Project → Owner → Contract) as a knowledge graph to eliminate topical noise.
*   **Agentic Workflows:** Moving from "Point-and-Click" retrieval to "Describe-and-Do" agents that perform multi-step reasoning across domain-specific data silos.

---

## 🔗 High-Fidelity Case Studies
Industry leaders are already moving beyond basic RAG into high-verification "Agentic" architectures:

*   **[KPMG's Ava Platform](https://www.techuk.org/resource/ai-adoption-case-study-kpmg-s-ava-gen-ai-tool-creates-useable-outputs-improves-efficiences-and-reduces-risk.html):** Implementing RAG-driven trust metrics to reduce risk and improve usability for enterprise outputs.
*   **[Nasdaq (Progress Software) RAG Platform](https://www.nasdaq.com/press-release/progress-software-unveils-breakthrough-saas-rag-platform-designed-make-trustworthy):** A breakthrough SaaS implementation focused specifically on "Trustworthy RAG" for high-compliance environments.
*   **[Autodesk Assistant Blueprint](https://aws.amazon.com/blogs/machine-learning/autodesk-assistant-building-an-agentic-platform-on-amazon-bedrock/):** Moving from search to reasoning by coordinating domain-specific agents to navigate complex technical regulations.

---

## 🚀 Strategic Open Questions for Q3/Q4
As we scale to production, the board should consider:
1.  **Trust Architecture:** Should we implement an automated "RAG Evaluation Judge" (like Nasdaq's REMi) to minimize human oversight?
2.  **Domain Silos:** How do we coordinate agents between dbt metadata, ODCS contracts, and Jira tickets without creating new knowledge silos?
3.  **Discovery vs. Action:** Can the assistant evolve from "Tell me the SLA" to "Draft a new Data Contract based on this schema"?

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
*Built for the AI Product Management Executive Capstone — DefTunes Project.*
