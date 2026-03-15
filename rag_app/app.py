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

# ==========================================
# SKYSCANNER-INSPIRED THEME + ROBOTO FONT
# ==========================================
st.markdown("""
<style>
    /* ── Import Roboto from Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    /* ── Global font & background ── */
    html, body, [class*="css"] {
        font-family: 'Roboto', sans-serif;
        color: #121234;
    }
    .stApp {
        background: linear-gradient(175deg, #f0f7ff 0%, #ffffff 40%, #f8fbff 100%);
    }

    /* ── Header ── */
    .stApp h1 {
        color: #0770E3;
        font-weight: 700;
        text-align: center;
        letter-spacing: -0.5px;
        padding-top: 0.5rem;
    }
    .stApp h2, .stApp h3 {
        color: #121234;
        font-weight: 500;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: #121234;
        color: #FFFFFF;
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }

    /* ── Sidebar metrics ── */
    section[data-testid="stSidebar"] [data-testid="stMetric"] {
        background-color: rgba(7, 112, 227, 0.15);
        border: 1px solid rgba(7, 112, 227, 0.3);
        border-radius: 10px;
        padding: 10px 14px;
    }
    section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
        color: #89b4fa !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-weight: 700;
    }

    /* ── Chat messages ── */
    [data-testid="stChatMessage"] {
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 4px rgba(18, 18, 52, 0.06);
        border: 1px solid #e8eef6;
        background-color: #FFFFFF;
    }

    /* ── Chat input ── */
    .stChatInput textarea {
        font-family: 'Roboto', sans-serif !important;
        border-radius: 10px !important;
        border: 2px solid #d0dff0 !important;
    }
    .stChatInput textarea:focus {
        border-color: #0770E3 !important;
        box-shadow: 0 0 0 2px rgba(7, 112, 227, 0.15) !important;
    }

    /* ── Buttons & links ── */
    .stButton > button {
        background-color: #0770E3;
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        font-family: 'Roboto', sans-serif;
    }
    .stButton > button:hover {
        background-color: #0560c4;
    }
    a { color: #0770E3; }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        font-family: 'Roboto', sans-serif;
        font-weight: 500;
        color: #121234;
    }

    /* ── Welcome blurb ── */
    .welcome-box {
        text-align: center;
        padding: 0.75rem 1rem;
        color: #3d3d6b;
        font-size: 1.02rem;
        line-height: 1.6;
    }

    /* ── Divider ── */
    hr { border-color: #d0dff0; }
</style>
""", unsafe_allow_html=True)

st.title("DefTunes Data Discoverability AI 🔍")
st.markdown("""
<div class="welcome-box">
Welcome to the DefTunes Data Product Knowledge Base!<br>
Ask me anything about our data tables, schema, SLAs, quality rules, and ownership.
</div>
""", unsafe_allow_html=True)

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

# WHY THIS PROMPT MATTERS (Guardrails)
# ------------------------------------
# As a Product Manager, the system prompt is the #1 lever for controlling AI quality.
# Two key techniques are at work here:
#   1. Role assignment — we tell the model "you are an expert DPM" so it stays
#      focused on data product language and avoids generic answers.
#   2. Negative constraint — the explicit "if you don't know, say so" instruction
#      dramatically reduces hallucinations, which is the biggest trust risk
#      for any enterprise AI feature.

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
# SIDEBAR: SAMPLE QUESTIONS
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
# SIDEBAR: COST DASHBOARD (cumulative)
# ==========================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Cost Dashboard")

if "total_prompt_tokens" not in st.session_state:
    st.session_state.total_prompt_tokens = 0
    st.session_state.total_output_tokens = 0
    st.session_state.total_cost = 0.0
    st.session_state.query_count = 0

col_s1, col_s2 = st.sidebar.columns(2)
col_s1.metric("Queries", st.session_state.query_count)
col_s2.metric("Total Cost", f"${st.session_state.total_cost:.5f}")

col_s3, col_s4 = st.sidebar.columns(2)
col_s3.metric("Prompt Tokens", st.session_state.total_prompt_tokens)
col_s4.metric("Output Tokens", st.session_state.total_output_tokens)

if st.session_state.query_count > 0:
    avg_cost = st.session_state.total_cost / st.session_state.query_count
    st.sidebar.caption(f"Avg cost per query: **${avg_cost:.5f}**")
else:
    st.sidebar.caption("Send a query to see live cost tracking.")

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
                # Retrieve relevant context from ChromaDB.
                # We fetch the top 5 matching chunks (k=5). This is the sweet spot:
                # fewer chunks risk missing important join context, while many more
                # add noise without improving accuracy — and inflate token costs.
                docs = vectorstore.similarity_search(prompt, k=5)
                context = "\n\n---\n\n".join([doc.page_content for doc in docs])
                
                # Build the full prompt by injecting the retrieved context directly.
                # This "context stuffing" approach works well with Gemini 2.0 Flash's
                # large context window.  As a PM, we keep an eye on the input token
                # volume here because it directly drives per-query cost.
                full_prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {prompt}\n\nHelpful Answer:"
                
                # Call Gemini
                response = model.generate_content(full_prompt)
                answer = response.text
                
                # Track unit economics — every query costs money, so we log it.
                usage = response.usage_metadata
                prompt_tokens = usage.prompt_token_count
                output_tokens = usage.candidates_token_count
                # Gemini 2.0 Flash Pricing (Est): $0.10 per 1M input, $0.40 per 1M output
                est_cost = (prompt_tokens * 0.10 / 1_000_000) + (output_tokens * 0.40 / 1_000_000)
                
                # Update cumulative sidebar metrics
                st.session_state.total_prompt_tokens += prompt_tokens
                st.session_state.total_output_tokens += output_tokens
                st.session_state.total_cost += est_cost
                st.session_state.query_count += 1
                
                st.markdown(answer)
                
                with st.expander("📄 View Source Context"):
                    for doc in docs:
                        st.markdown(f"**Source:** `{doc.metadata.get('source', 'Unknown')}` | **Type:** {doc.metadata.get('type', '')}")
                        st.code(doc.page_content, language="yaml")
                        
                st.session_state.messages.append({"role": "assistant", "content": answer})

                # Force a rerun so sidebar metrics update immediately
                st.rerun()
            except Exception as e:
                st.error(f"Error querying Gemini: {e}")
