# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "spotipy",
#     "python-dotenv",
# ]
# ///

"""Back up Spotify liked songs, saved albums, playlists, and followed artists.

Usage:
    uv run backup.py login    # Authenticate with Spotify (opens browser)
    uv run backup.py          # Run backup (requires prior login)
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

BACKUP_DIR = Path(__file__).parent
CACHE_PATH = BACKUP_DIR / ".spotify_cache"
SCOPE = "user-library-read playlist-read-private user-follow-read"
PAGE_SIZE = 50


def build_auth_manager() -> SpotifyOAuth:
    load_dotenv()

    client_id = os.environ.get("SPOTIPY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    if not client_id or not client_secret:
        print("Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET.")
        print("Set them in .env or as environment variables.")
        print("Create a Spotify app at https://developer.spotify.com/dashboard")
        raise SystemExit(1)

    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPE,
        cache_path=str(CACHE_PATH),
    )


def login():
    auth_manager = build_auth_manager()
    auth_manager.get_access_token(as_dict=False)
    print("Authenticated successfully. Token cached at .spotify_cache")


def authenticate() -> spotipy.Spotify:
    auth_manager = build_auth_manager()
    token = auth_manager.get_cached_token()

    if not token:
        print("No cached token found. Run 'uv run backup.py login' first.")
        raise SystemExit(1)

    return spotipy.Spotify(auth_manager=auth_manager)


def fetch_all(sp: spotipy.Spotify, fetch_fn, label: str) -> list[dict]:
    """Paginate an endpoint that uses limit/offset."""
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


def fetch_followed_artists(sp: spotipy.Spotify) -> list[dict]:
    """Paginate followed artists (cursor-based, not offset-based)."""
    artists = []
    after = None

    while True:
        result = sp.current_user_followed_artists(limit=PAGE_SIZE, after=after)
        page = result["artists"]
        batch = page["items"]
        if not batch:
            break
        artists.extend(batch)
        print(f"  Fetched {len(artists)} / {page['total']} artists...")
        after = batch[-1]["id"]

    return artists


def fetch_playlists_with_tracks(sp: spotipy.Spotify) -> list[dict]:
    """Fetch all playlists, then fetch full track listings for each."""
    playlists = fetch_all(sp, sp.current_user_playlists, "playlists")

    for i, playlist in enumerate(playlists):
        name = playlist["name"]
        playlist_id = playlist["id"]
        print(f"  [{i + 1}/{len(playlists)}] Fetching tracks for '{name}'...")

        tracks = []
        offset = 0
        while True:
            page = sp.playlist_items(playlist_id, limit=PAGE_SIZE, offset=offset)
            batch = page["items"]
            if not batch:
                break
            tracks.extend(batch)
            offset += PAGE_SIZE

        playlist["tracks_backup"] = tracks

    return playlists


def save(data, path: Path) -> None:
    if isinstance(data, list):
        data.sort(key=lambda item: item.get("added_at", ""))
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved to {path}")


def backup():
    sp = authenticate()

    print("Fetching liked songs...")
    tracks = fetch_all(sp, sp.current_user_saved_tracks, "tracks")
    print(f"Total: {len(tracks)} liked songs")
    save(tracks, BACKUP_DIR / "liked_songs.json")

    print("\nFetching saved albums...")
    albums = fetch_all(sp, sp.current_user_saved_albums, "albums")
    print(f"Total: {len(albums)} saved albums")
    save(albums, BACKUP_DIR / "saved_albums.json")

    print("\nFetching playlists...")
    playlists = fetch_playlists_with_tracks(sp)
    print(f"Total: {len(playlists)} playlists")
    save(playlists, BACKUP_DIR / "playlists.json")

    print("\nFetching followed artists...")
    artists = fetch_followed_artists(sp)
    print(f"Total: {len(artists)} followed artists")
    save(artists, BACKUP_DIR / "followed_artists.json")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "backup"

    match command:
        case "login":
            login()
        case "backup":
            backup()
        case _:
            print(f"Unknown command: {command}")
            print("Usage: uv run backup.py [login|backup]")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
