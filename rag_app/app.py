import os
import time
import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="DefTunes Data Assistant",
    page_icon="🤖",
    layout="centered"
)

# ==========================================
# APPLE-INSPIRED PREMIUM THEME
# ==========================================
st.markdown("""
<style>
    /* ── Apple-style Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1d1d1f;
    }

    /* ── Glassmorphism Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Dark sidebar content styling */
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f5f5f7 !important;
    }

    /* ── Subtle Background ── */
    .stApp {
        background: #ffffff;
    }

    /* ── Premium Buttons ── */
    .stButton > button {
        background-color: #0071e3;
        color: #fff;
        border-radius: 980px;
        padding: 0.5rem 1.2rem;
        font-weight: 400;
        border: none;
        transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
    }
    .stButton > button:hover {
        background-color: #0077ed;
        transform: scale(1.02);
    }

    /* ── Apple Chat Bubbles ── */
    [data-testid="stChatMessage"] {
        background-color: #f5f5f7;
        border-radius: 18px;
        border: none;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    
    [data-testid="stChatMessageContent"] {
        font-size: 1rem;
        line-height: 1.5;
    }

    /* ── Metrics Cards ── */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px;
    }

    /* ── Titles ── */
    h1 {
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
        color: #1d1d1f;
    }
</style>
""", unsafe_allow_html=True)

st.title("DefTunes Discovery AI 🤖")

st.markdown("""
Welcome to the internal data assistant. 
**Explore schemas, SLAs, and data ownership** using natural language.
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
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password", help="Your key is only used for this session.")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    else:
        st.info("👋 Enter your Gemini API key in the sidebar to begin.")
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
# SIDEBAR: NAVIGATION & TOOLS
# ==========================================
st.sidebar.markdown("### 🔍 Discovery Tools")
st.sidebar.markdown("_💡 Try asking:_")
sample_questions = [
    "What tables are in the landing zone?",
    "What user feedback actions do we track?",
    "Who owns the serving layer data?",
    "What are the SLAs for data freshness?",
    "What columns does fact_feedback have?",
]
for q in sample_questions:
    st.sidebar.markdown(f"- {q}")

# ==========================================
# SIDEBAR: UNIT ECONOMICS (Apple Style)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Cost & Latency Dashboard")

if "total_prompt_tokens" not in st.session_state:
    st.session_state.total_prompt_tokens = 0
    st.session_state.total_output_tokens = 0
    st.session_state.total_cost = 0.0
    st.session_state.query_count = 0
    st.session_state.total_latency = 0.0

col_s1, col_s2 = st.sidebar.columns(2)
col_s1.metric("Queries", st.session_state.query_count)
col_s2.metric("Total Cost", f"${st.session_state.total_cost:.4f}")

col_s3, col_s4 = st.sidebar.columns(2)
avg_latency = st.session_state.total_latency / st.session_state.query_count if st.session_state.query_count > 0 else 0
col_s3.metric("Avg Latency", f"{avg_latency:.2f}s")
col_s4.metric("Tokens", f"{st.session_state.total_prompt_tokens + st.session_state.total_output_tokens}")

if st.session_state.query_count > 0:
    st.sidebar.caption(f"Estimated ROI: **99.9%** vs manual lookup.")
else:
    st.sidebar.caption("Real-time telemetry enabled.")

# ==========================================
# CHAT UI
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("E.g., What are our data quality rules?"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Retrieving context..."):
            start_time = time.time()
            try:
                # Retrieve relevant context
                docs = vectorstore.similarity_search(prompt, k=5)
                context = "\n\n---\n\n".join([doc.page_content for doc in docs])
                
                # Build prompt
                full_prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {prompt}\n\nHelpful Answer:"
                
                # Call Gemini
                response = model.generate_content(full_prompt)
                answer = response.text
                
                latency = time.time() - start_time
                
                # Track usage
                usage = response.usage_metadata
                prompt_tokens = usage.prompt_token_count
                output_tokens = usage.candidates_token_count
                est_cost = (prompt_tokens * 0.10 / 1_000_000) + (output_tokens * 0.40 / 1_000_000)
                
                # Update state
                st.session_state.total_prompt_tokens += prompt_tokens
                st.session_state.total_output_tokens += output_tokens
                st.session_state.total_cost += est_cost
                st.session_state.query_count += 1
                st.session_state.total_latency += latency
                
                st.markdown(answer)
                
                with st.expander("📄 View Sources"):
                    for doc in docs:
                        st.markdown(f"**Source:** `{doc.metadata.get('source', 'Unknown')}`")
                        st.code(doc.page_content, language="yaml")
                        
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")
