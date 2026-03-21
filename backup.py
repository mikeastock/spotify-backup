# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "spotipy",
#     "python-dotenv",
# ]
# ///

"""Back up Spotify liked songs and saved albums."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

BACKUP_DIR = Path(__file__).parent
CACHE_PATH = BACKUP_DIR / ".spotify_cache"
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


def fetch_all(sp: spotipy.Spotify, fetch_fn, label: str) -> list[dict]:
    items = []
    offset = 0

    while True:
        page = fetch_fn(limit=PAGE_SIZE, offset=offset)
        batch = page["items"]
        if not batch:
            break
        items.extend(batch)
        print(f"  Fetched {len(items)} / {page['total']} {label}...")
        offset += PAGE_SIZE

    return items


def save(items: list[dict], path: Path) -> None:
    items.sort(key=lambda item: item["added_at"])
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved to {path}")


def main():
    print("Authenticating with Spotify...")
    sp = authenticate()

    print("Fetching liked songs...")
    tracks = fetch_all(sp, sp.current_user_saved_tracks, "tracks")
    print(f"Total: {len(tracks)} liked songs")
    save(tracks, BACKUP_DIR / "liked_songs.json")

    print("\nFetching saved albums...")
    albums = fetch_all(sp, sp.current_user_saved_albums, "albums")
    print(f"Total: {len(albums)} saved albums")
    save(albums, BACKUP_DIR / "saved_albums.json")


if __name__ == "__main__":
    main()
