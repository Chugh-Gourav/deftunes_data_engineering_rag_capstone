"""
DefTunes Data Generator
=======================
Generates synthetic datasets that simulate a music streaming platform's core data assets.
This script is the first step in the DefTunes data pipeline, producing four datasets:

1. Users       — 5,000 realistic user profiles (via Random User API)
2. Songs       — 1,000 real song records (via iTunes Search API)
3. Sessions    — 100,000 simulated listening events
4. Feedback    — 50,000 explicit user interactions (likes, dislikes, skips, playlist adds)

Product Context:
    As a Data/AI Product Manager, understanding the shape and distribution of your data
    is critical. This generator simulates realistic user behavior patterns:
    - Feedback weights (50% likes, 30% skips, 10% dislikes, 10% playlist adds) 
      reflect typical music streaming engagement patterns observed in the industry.
    - Sessions simulate a 30-day rolling window of listening activity.
    - All output is in NDJSON (Newline Delimited JSON) format, which is the preferred
      ingestion format for Google BigQuery's auto-schema detection.

Usage:
    python generate_data.py
"""

import json
import random
import uuid
import time
from datetime import datetime, timedelta
import requests

# ──────────────────────────────────────────────────────────────────────────
# DATA VOLUME CONSTANTS
# These values control the scale of the generated datasets.
# In a production setting, these would come from a config file or env vars.
# ──────────────────────────────────────────────────────────────────────────
NUM_USERS = 5000
NUM_SONGS = 1000
NUM_SESSIONS = 100000
NUM_FEEDBACK = 50000


def generate_users(num_users: int) -> list:
    """
    Generates realistic user profiles using the Random User Generator API.
    
    Product Rationale:
        Using a real-world API for user data (rather than pure random generation)
        gives us realistic name distributions, geographic diversity, and 
        registration date patterns — making downstream analytics more meaningful.
    """
    print(f"Generating {num_users} users...")
    users = []
    
    # Random User API supports up to 5,000 results per request
    # We filter to English-speaking countries for name consistency
    response = requests.get(
        f"https://randomuser.me/api/?results={num_users}&inc=name,registered,location,login&nat=us,gb,ca,au"
    )
    
    if response.status_code == 200:
        data = response.json()['results']
        for user in data:
            users.append({
                "user_id": user['login']['uuid'],
                "user_name": user['name']['first'],
                "user_lastname": user['name']['last'],
                "user_since": user['registered']['date'][:10],  # YYYY-MM-DD format
                "place_name": user['location']['city'],
                "country_code": user['location']['country']
            })
    return users


def fetch_itunes_songs(num_songs: int) -> list:
    """
    Fetches real song metadata from the Apple iTunes Search API.
    
    Product Rationale:
        Using real song data (titles, artists, genres) rather than synthetic data
        makes the RAG discoverability layer more compelling — users can ask about
        actual artists and get meaningful responses from the knowledge base.
    
    API Notes:
        - iTunes Search API is free, requires no authentication
        - Limited to 200 results per request, so we iterate through genres
        - We deduplicate by song_id to avoid inflated catalog counts
    """
    print(f"Fetching {num_songs} real songs from iTunes Search API...")
    songs = []
    
    # Genre diversity ensures a representative music catalog
    genres = ["pop", "rock", "hip-hop", "jazz", "classical", "electronic", "country", "rnb"]
    
    for genre in genres:
        if len(songs) >= num_songs:
            break
            
        url = f"https://itunes.apple.com/search?term={genre}&entity=song&limit=200"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                for track in results:
                    if len(songs) >= num_songs:
                        break
                    
                    song_id = str(track.get('trackId', uuid.uuid4()))
                    track_id = f"TRK-{song_id}"
                    title = track.get('trackName', 'Unknown Title')
                    artist_id = str(track.get('artistId', uuid.uuid4()))
                    artist_mbid = f"itunes-arti-{artist_id}"
                    artist_name = track.get('artistName', 'Unknown Artist')
                    
                    # Parse release year from ISO date string
                    year = 2024
                    release_date = track.get('releaseDate', '')
                    if release_date and len(release_date) >= 4:
                        try:
                            year = int(release_date[:4])
                        except ValueError:
                            pass
                    
                    release_type = track.get('primaryGenreName', 'Pop')
                    
                    # Skip duplicates — same song can appear in multiple genre searches
                    if any(s['song_id'] == str(song_id) for s in songs):
                        continue
                        
                    songs.append({
                        "song_id": str(song_id),
                        "track_id": track_id,
                        "title": title,
                        "release": release_type,
                        "year": year,
                        "artist_id": str(artist_id),
                        "artist_mbid": artist_mbid,
                        "artist_name": artist_name
                    })
            else:
                print(f"iTunes API error: {response.status_code}")
                
        except Exception as e:
            print(f"Error fetching genre {genre}: {e}")
            break
            
    print(f"Successfully fetched {len(songs)} songs from iTunes.")
    
    # Fallback: fill remaining slots with synthetic songs if API didn't return enough
    while len(songs) < num_songs:
        songs.append({
            "song_id": str(uuid.uuid4()),
            "track_id": f"TRK-{random.randint(100000, 999999)}",
            "title": f"Fallback Song {uuid.uuid4().hex[:8]}",
            "release": "Pop",
            "year": 2024,
            "artist_id": str(uuid.uuid4()),
            "artist_mbid": str(uuid.uuid4()), 
            "artist_name": "Fallback Artist"
        })
    return songs


def generate_sessions(users: list, songs: list, num_sessions: int) -> list:
    """
    Simulates listening sessions — the core behavioral event in a music platform.
    
    Product Rationale:
        Sessions represent the "heartbeat" of user engagement. Each session links
        a user to a song at a specific timestamp, forming the basis for:
        - Listening trend analysis (which artists are trending?)
        - User engagement metrics (sessions per user per day)
        - Cohort analysis (how do new users differ from veteran users?)
    """
    print(f"Generating {num_sessions} sessions...")
    sessions = []
    
    # Simulate a 30-day activity window (typical analytics lookback period)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    for _ in range(num_sessions):
        user = random.choice(users)
        song = random.choice(songs)
        
        random_seconds = random.randint(0, int((end_date - start_date).total_seconds()))
        session_time = start_date + timedelta(seconds=random_seconds)
        
        sessions.append({
            "session_id": str(uuid.uuid4()),
            "user_id": user["user_id"],
            "song_id": song["song_id"],
            "artist_id": song["artist_id"],
            "session_start_time": session_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return sessions


def generate_feedback(users: list, songs: list, num_feedback: int) -> list:
    """
    Generates explicit user feedback events (likes, dislikes, skips, playlist adds).
    
    Product Rationale:
        Explicit feedback is the highest-signal data for recommendation systems.
        The weighted distribution reflects real-world behavior:
        - 50% LIKE      → Users engage positively with about half of content they interact with
        - 30% SKIP       → Skip is the most common "negative" signal (passive rejection)
        - 10% DISLIKE    → Active dislikes are rare but high-signal for personalization
        - 10% ADD_TO_PLAYLIST → Strongest positive signal; indicates intent to re-listen
        
        This distribution is intentional — it mirrors industry benchmarks from Spotify
        and Apple Music engagement reports, making our analytics realistic.
    """
    print(f"Generating {num_feedback} explicit user feedbacks...")
    feedback_records = []
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Feedback action types with realistic probability weights
    types = ["LIKE", "DISLIKE", "SKIP", "ADD_TO_PLAYLIST"]
    weights = [0.5, 0.1, 0.3, 0.1]
    
    for _ in range(num_feedback):
        user = random.choice(users)
        song = random.choice(songs)
        
        random_seconds = random.randint(0, int((end_date - start_date).total_seconds()))
        feedback_time = start_date + timedelta(seconds=random_seconds)
        
        action = random.choices(types, weights=weights)[0]
        
        feedback_records.append({
            "feedback_id": str(uuid.uuid4()),
            "user_id": user["user_id"],
            "song_id": song["song_id"],
            "action": action,
            "timestamp": feedback_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return feedback_records


# ──────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# Orchestrates the full data generation pipeline and writes NDJSON output.
# ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    users = generate_users(NUM_USERS)
    songs = fetch_itunes_songs(NUM_SONGS)
    sessions = generate_sessions(users, songs, NUM_SESSIONS)
    feedbacks = generate_feedback(users, songs, NUM_FEEDBACK)
    
    # Write as NDJSON — one JSON object per line (BigQuery's preferred format)
    print("Writing files as NDJSON...")
    def write_ndjson(filename, data):
        with open(filename, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
                
    write_ndjson("users.json", users)
    write_ndjson("songs.json", songs)
    write_ndjson("sessions.json", sessions)
    write_ndjson("user_song_feedback.json", feedbacks)
        
    print(f"✅ Generated: {len(users)} users, {len(songs)} songs, {len(sessions)} sessions, {len(feedbacks)} interactions.")
