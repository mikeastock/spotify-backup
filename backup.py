# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "spotipy",
#     "python-dotenv",
# ]
# ///

"""Back up Spotify liked songs to liked_songs.json."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

BACKUP_FILE = Path(__file__).parent / "liked_songs.json"
CACHE_PATH = Path(__file__).parent / ".spotify_cache"
SCOPE = "user-library-read"
PAGE_SIZE = 50


def authenticate() -> spotipy.Spotify:
    load_dotenv()

    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    if not client_id or not client_secret:
        print("Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET.")
        print("Set them in .env or as environment variables.")
        print("Create a Spotify app at https://developer.spotify.com/dashboard")
        raise SystemExit(1)

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPE,
        cache_path=str(CACHE_PATH),
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def fetch_all_liked_songs(sp: spotipy.Spotify) -> list[dict]:
    tracks = []
    offset = 0

    while True:
        page = sp.current_user_saved_tracks(limit=PAGE_SIZE, offset=offset)
        items = page["items"]
        if not items:
            break
        tracks.extend(items)
        print(f"  Fetched {len(tracks)} / {page['total']} tracks...")
        offset += PAGE_SIZE

    return tracks


def main():
    print("Authenticating with Spotify...")
    sp = authenticate()

    print("Fetching liked songs...")
    tracks = fetch_all_liked_songs(sp)
    print(f"Total: {len(tracks)} liked songs")

    tracks.sort(key=lambda t: t["added_at"])

    BACKUP_FILE.write_text(json.dumps(tracks, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved to {BACKUP_FILE}")


if __name__ == "__main__":
    main()
