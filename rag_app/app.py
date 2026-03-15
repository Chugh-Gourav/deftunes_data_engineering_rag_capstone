import os
import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="DefTunes Data Discoverability AI",
    page_icon="🔍",
    layout="centered"
)

st.title("DefTunes Data Discoverability AI 🔍")
st.markdown("""
Welcome to the DefTunes Data Product Knowledge Base!  
Ask me anything about our data tables, schema, SLAs, quality rules, and ownership.
""")

# ==========================================
# SYSTEM PROMPT
# ==========================================
SYSTEM_PROMPT = """You are an expert Data Product Manager for the DefTunes music streaming platform.
Use the provided metadata and Open Data Contracts (ODCS) context to answer the user's questions about our data ecosystem.

Our data pipeline has three layers:
- Landing Zone (deftunes_landing_zone): Raw NDJSON data loaded from GCS — users, songs, sessions, and user feedback.
- Transform Layer (deftunes_transform_db): Cleaned dimensional models via dbt — fact_session, fact_feedback, dim_artists, dim_songs, dim_users.
- BI Views: Aggregated interaction metrics — interactions_per_artist_vw, interactions_per_country_vw.

User feedback actions include: LIKE, DISLIKE, SKIP, and ADD_TO_PLAYLIST.

If you don't know the answer based strictly on the context, say "I don't have information about that in the current data contracts."
Do not make up column names, SLAs, or metrics that are not in the context."""

"""
PM CONTEXT: SYSTEM PROMPT ENGINEERING
This prompt serves as the 'Guardrails' for our AI Product. 
By identity-anchoring ("You are an expert DPM") and providing a clear 
'Negative Constraint' (If you don't know, say so), we reduce hallucination 
rates—one of the top concerns for enterprise AI products.
"""

# ==========================================
# INITIALIZE RAG SYSTEM
# ==========================================
@st.cache_resource
def init_vectorstore():
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    if not os.path.exists("./chroma_db"):
        st.error("Vector database not found! Please run `python ingest.py` first.")
        st.stop()
        
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    return vectorstore

# Check for API Key
if "GOOGLE_API_KEY" not in os.environ:
    api_key = st.sidebar.text_input("Enter your Gemini API Key", type="password")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    else:
        st.warning("Please provide a Gemini API Key to use the RAG system.")
        st.stop()

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Initialize components
try:
    vectorstore = init_vectorstore()
    model = genai.GenerativeModel("gemini-2.0-flash")
except Exception as e:
    st.error(f"Failed to initialize RAG system: {e}")
    st.stop()

# ==========================================
# SAMPLE QUESTIONS
# ==========================================
st.sidebar.markdown("### 💡 Try asking:")
sample_questions = [
    "What tables are in the landing zone?",
    "What user feedback actions do we track?",
    "Who owns the serving layer data?",
    "What are the SLAs for data freshness?",
    "What quality rules exist for our data?",
    "What columns does fact_feedback have?",
]
for q in sample_questions:
    st.sidebar.markdown(f"- {q}")

# ==========================================
# CHAT UI
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("E.g., What feedback actions do we track?"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Searching data contracts..."):
            try:
                # Retrieve relevant context from ChromaDB
                # PM CONTEXT: THE 'K-VALUE' TRADEOFF
                # We fetch k=5 chunks (approx. 1500-2000 tokens). This hits the 'Sweet Spot':
                # - Low K (<3): Missing join context (e.g. users vs songs).
                # - High K (>10): Noise injection, higher latency, and increased token costs.
                docs = vectorstore.similarity_search(prompt, k=5)
                context = "\n\n---\n\n".join([doc.page_content for doc in docs])
                
                # Build the full prompt
                # PM CONTEXT: CONTEXT STUFFING
                # We inject retrieved snippets directly into the LLM prompt.
                # Gemini 2.0 Flash's large window handles this easily, but as a PM, 
                # we track 'Input Token' volume here to manage unit economics ($0.0003/query).
                full_prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {prompt}\n\nHelpful Answer:"
                
                # Call Gemini
                response = model.generate_content(full_prompt)
                answer = response.text
                
                # PM CONTEXT: UNIT ECONOMICS TRACKING
                usage = response.usage_metadata
                prompt_tokens = usage.prompt_token_count
                output_tokens = usage.candidates_token_count
                # Gemini 2.0 Flash Pricing (Est): $0.10 per 1M input, $0.40 per 1M output
                est_cost = (prompt_tokens * 0.10 / 1_000_000) + (output_tokens * 0.40 / 1_000_000)
                
                st.markdown(answer)
                
                with st.expander("📊 View AI Unit Economics"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Prompt Tokens", prompt_tokens)
                    col2.metric("Output Tokens", output_tokens)
                    col3.metric("Est. Cost", f"${est_cost:.5f}")
                    st.info(f"PM Insight: By using RAG (k=5), we filtered out ~70% of the Knowledge Base, saving significant token budget.")

                with st.expander("📄 View Source Context"):
                    for doc in docs:
                        st.markdown(f"**Source:** `{doc.metadata.get('source', 'Unknown')}` | **Type:** {doc.metadata.get('type', '')}")
                        st.code(doc.page_content, language="yaml")
                        
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Error querying Gemini: {e}")
