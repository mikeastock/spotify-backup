# spotify-backup

Back up your Spotify liked songs to a JSON file, tracked in git.

## Setup

1. Create a Spotify app at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Set the redirect URI to `http://127.0.0.1:8888/callback`
3. Copy `.env.example` to `.env` and fill in your credentials:

```sh
cp .env.example .env
```

## Usage

```sh
uv run backup.py
```

On first run, a browser window opens for Spotify authorization. The token is cached in `.spotify_cache` for subsequent runs.

## Output

`liked_songs.json` — full Spotify API response for every liked song, sorted by `added_at`. Commit it to git to track changes over time.
