import os
import google.generativeai as genai

# Setup
# PM CONTEXT: We use environment variables for API keys to maintain security 
# and portability across production environments.
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    # Defaulting to the demo key for user convenience in this local prototype
    api_key = "AQ.Ab8RN6J9oO3UvdWuq7f3TIQMDkbd2_q-xqTRtYp1SZpWOmBVLQ"

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

system_prompt = """You are an expert Data Product Manager for the DefTunes music streaming platform.
Use the provided metadata and Open Data Contracts (ODCS) context to answer the user's questions about our data ecosystem."""

# Simulate 5 average chunks (approx 300 words each)
# PM CONTEXT: This mock context represents a typical k=5 retrieval payload in a RAG system.
mock_context = """
CHUNK 1: Table raw_users. Columns: user_id (string), user_name (string), user_since (date), country_code (string).
CHUNK 2: Table raw_user_feedback. Columns: feedback_id (string), user_id (string), action (string), timestamp (timestamp). Quality rules: accepted_values [LIKE, DISLIKE, SKIP].
CHUNK 3: Table dim_artists (dbt). Columns: artist_id (string), artist_name (string).
CHUNK 4: View interactions_per_country_vw. Aggregated by year, month, country_code.
CHUNK 5: SLA: Freshness 24h, Availability 99.9%. Owner: Data Engineering.
"""

question = "What tables and columns do I need to join to see likes by artist name and user country?"

full_prompt = f"{system_prompt}\n\nContext:\n{mock_context}\n\nQuestion: {question}\n\nHelpful Answer:"

# Execute Generation
response = model.generate_content(full_prompt)
usage = response.usage_metadata

print("--- AI TOKEN ECONOMICS BENCHMARK ---")
print(f"PROMPT_TOKENS: {usage.prompt_token_count}")
print(f"OUTPUT_TOKENS: {usage.candidates_token_count}")
print(f"EST_COST (USD): ${((usage.prompt_token_count * 0.10 / 1_000_000) + (usage.candidates_token_count * 0.40 / 1_000_000)):.6f}")
print(f"SAMPLE RESPONSE: {response.text[:100]}...")
print("------------------------------------")
