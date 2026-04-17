

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

def load_API():
    load_dotenv("spodify.env")

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri="http://127.0.0.1:3000",
        scope="playlist-read-private playlist-read-collaborative"
    ))
    return sp
        
def fetch_playlist_ID(url): 
    playlist_ID = url.split("/playlist/")[1].split("?")[0]
    return playlist_ID

def strip_playlist(sp,playlist_ID):
    results = sp.playlist_tracks(playlist_ID)
    with open("playlist_data.txt", "w", encoding="utf-8") as f:
        for item in results['items']:
            track = item.get('track') or item.get('item')
            if track:
                line = f"{track['name']} - {track['artists'][0]['name']} - {track['album']['name']}"
                f.write(line + "\n")

def main():
    sp = load_API()
    users_playlist = input("Please enter a spodify PUBLIC playlist: ")
    playlist_ID = fetch_playlist_ID(users_playlist)
    strip_playlist(sp,playlist_ID)

    print("file is done being written")

main()



