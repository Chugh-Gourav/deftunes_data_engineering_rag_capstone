"""
Spotify API Connectivity Test
==============================
Quick validation script to test Spotify Web API authentication.

Product Context:
    This was originally explored as the primary data source for song metadata.
    Spotify's free-tier API restrictions limited our access, so we pivoted to the 
    Apple iTunes Search API (see generate_data.py). This script is retained as
    documentation of the API evaluation process — a common PM task when selecting
    data sources for a data product.
"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import sys

client_id = "YOUR_SPOTIFY_CLIENT_ID"
client_secret = "YOUR_SPOTIFY_CLIENT_SECRET"

try:
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    results = sp.search(q='weaver', limit=1)
    print("Success:", results['tracks']['items'][0]['name'])
except Exception as e:
    print("Error:", e)
