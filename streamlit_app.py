"""
Polished UI for product. 
Streamlit is used for User Interface.
"""

import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
import sys
import os
import re

st.set_page_config(page_title="AI Song & Caption Generatror", page_icon="🎶", layout="centered")

def load_API():
    load_dotenv("spodify.env")
    load_dotenv("gemini.env")

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri="http://127.0.0.1:3000",
        scope="playlist-read-private playlist-read-collaborative"
    ))

    client = genai.Client(api_key=os.getenv("GEMINI_API"))

    return sp, client

def fetch_playlist_ID(url): 
    playlist_ID = url.split("/playlist/")[1].split("?")[0]
    return playlist_ID

def strip_playlist(sp,playlist_ID):
    playlist_songs = []
    results = sp.playlist_tracks(playlist_ID)
    for item in results['items']:
            track = item.get('track') or item.get('item')
            if track:
                song = f"{track['name']}"
                artist = f"{track['artists'][0]['name']}"
                album =f" {track['album']['name']}"

                track_info = [song, artist, album]
                playlist_songs.append(track_info)
    return(playlist_songs)

def extract_json_output(ai_output):
    try:
        return json.loads(ai_output)
    except json.JSONDecodeError:
        searching_for_json_object = re.search(r"(\{.*\})", ai_output, re.DOTALL)
        wanted_text = ""
        if searching_for_json_object:
            wanted_text = searching_for_json_object.group(1)
        else:
            if ai_output.startswith("{"):
                wanted_text = ai_output
            else:
                st.error("AI did not return valid JSON/valid JSON not found.")
                st.stop()

def main():

    if "track_information" not in st.session_state:
        st.session_state.track_information = None
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = None

    sp, client = load_API()

    st.title("🎶 AI Song & Caption Generator")
    st.markdown("" \
    "**Spodify Playlist Upload:**" \
    "\n   - Needs the **FULL URL** to fetch a playlist." \
    "\n   - Playlist needs to be **public** and less than 100 tracks.")

    provided_playlist = st.text_input("Provide your Public Spotify Playlist URL: ")

    st.markdown("**Post Information:**\n\n - Give a short description of what your post is about.")
    post_description = st.text_input("Give a short description of what your post is about: ")

    if st.button("Create your Dream Post"):
        if not provided_playlist or not post_description: 
            st.warning("Provide a Public Playlist URL and a post description.")
            st.stop()

        with st.spinner("Fetching tracks..."):
            playlist_ID = fetch_playlist_ID(provided_playlist)
            if not playlist_ID:
                st.error("Invalid playlist URL. Try Again")
                st.stop()

            try:
                st.session_state.track_information = strip_playlist(sp, playlist_ID)
                st.success("Playlist successfully fetched.")
            except Exception as e:
                st.error(f"Failed to fetch playlist: {e}")
                st.stop()

        with st.spinner("Creating your dream post..."):
            system_instructions = ("You are a trendy music and social media expert that will pick a song from a user that would best fit their description of their post"
                                "Don't use any songs out side of the provided songs unless the user asks for suggestions not on the playlist."
                                "Captions should be gnerated based on the description of the post or music if its relevent to the description"
                                "Format of JSON is top songs you found  are in order and songs are matched with their reasoning in order so that if you turned it into a list it would be indexable so song[0] would be the song to reasoning[0]"
                                "JSON has 3 keys named songs (stores the top 3 song recommendations), reasoning(store matching explenations), and captions(have captions ready for users in case they want them)"
                                )
            config = types.GenerateContentConfig(
            system_instruction=system_instructions,
            temperature=0.2,
            top_p=0.9,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="application/json"
            )

            song_recommendation_instructions = [ f"Please genertate exactly 3 song recommendations from the songs provided from {st.session_state.track_information} for each recommendation provoide a resoning "
                                            f"Use the description of the post to do a vibe check, check the songs to see which ones best match the users posts description/vibe use {post_description} for this"
                                            f"Generate potential captions also using the description {post_description}"
                                            f"don't repeat any of the songs you already have on the list"
                                            "JSON should include: "
                                            "Each entry in the 'songs' list must be a LIST itself containing [Song Name, Artist Name, Album Name].",
                                            "For example,['Song 1', 'Artist 1', 'Album 1'], ['Song 2', 'Artist 2', 'Album 2']]",
                                            f"1. songs: (list of lists) the top 3 recommendations from the playlist provided that best matches the descristion and vibe of the post"
                                            f"2. reasoning: (list of strings) recommendations reasonings. why should the user pick this song? MATCH WITH SONG ORDER"
                                            f"3. captions: (list of strings) captions that a user could use in their instagram/facebook/ other social media post based on descirption"
                                            f"don't use any tracks that aren't on the song list provided"
                                            f"only out put in TRUE JASON formate" ]
        response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=song_recommendation_instructions, 
        config=config                  
        )

        json_output = extract_json_output(response.text.strip())

        if len(json_output["songs"]) != len(json_output["reasoning"]):
            st.error("Mismatch between number of song and reasonings.")
            st.stop()

        st.session_state.recommendations = json_output
        st.session_state.model_output_text = response.text.strip()
        # Initialize previous songs with the original recommendations to avoid duplicates
        st.session_state.previous_songs = json_output["songs"].copy()

    if st.session_state.recommendations:
        st.subheader("YOUR TOP SONG CHOICES HAVE BEEN CALCULATED! 𝄞⨾𓍢ִ໋")

        song = st.session_state.recommendations["songs"]
        reasoning = st.session_state.recommendations["reasoning"]
        captions = st.session_state.recommendations["captions"]

        for i in range(len(song)):
            with st.expander(f"Recommendation {i+1}:  **{song[i][0]} by {song[i][1]}**", expanded = True):
                st.markdown(f"**Album:** {song[i][2]}")
                st.markdown(f"**Reasoning:** {reasoning[i]}")

            # st.markdown(f"﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌Recommendation {i+1}﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌")
            # st.markdown(f"╰┈➤Song: {song[i][0]}")
            # st.markdown(f"    ♪Artist: {song[i][1]}\n")
            # st.markdown(f"Reasoning: {reasoning[i]} \n")

        st.subheader("⊹ ࣪ ˖ Here are some captions we think you will like ⊹ ࣪ ˖: ")

        for i, cap in enumerate(captions):
            st.write(f"{i+1}. **{cap}**")

        st.divider()
        st.write("Weren't able to find a song for your post?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Get Different Recommendations!"):
                with st.spinner("Finding different songs for you..."):
                    config = types.GenerateContentConfig(
                        temperature=0.9,
                        response_mime_type="application/json",
                    )
                    
                    # Get songs already recommended to exclude them
                    previously_recommended = st.session_state.get("previous_songs", [])
                    previous_songs_str = "; ".join([f"{song[0]} by {song[1]}" for song in previously_recommended]) if previously_recommended else "None"
                    
                    # Create list of available songs (excluding previous ones)
                    available_songs = []
                    excluded_titles = {song[0].lower() for song in previously_recommended}
                    for song in st.session_state.track_information:
                        if song[0].lower() not in excluded_titles:
                            available_songs.append(song)
                    
                    available_songs_str = "; ".join([f"{song[0]} by {song[1]}" for song in available_songs[:30]])
                    
                    recommendation_instructions = [f"CRITICAL INSTRUCTION: Generate exactly 3 COMPLETELY NEW and DIFFERENT song recommendations."
                                        f"\nYou MUST ONLY choose from these songs: {available_songs_str}"
                                        f"\nYou MUST NEVER recommend ANY of these songs: {previous_songs_str}"
                                        f"\nFor each recommendation, provide reasoning on why it matches the vibe: {post_description}"
                                        f"\nGenerate new unique captions based on: {post_description}"
                                        "\nReturn ONLY valid JSON with these 3 keys:"
                                        "\n- songs: list of [Song Name, Artist Name, Album Name] (MUST be different from excluded list)"
                                        "\n- reasoning: list of reasoning for each song choice"
                                        "\n- captions: list of new unique captions"
                                        f"\nEXCLUDED (Never use): {previous_songs_str}"
                                        f"\nALLOWED (Only use): {available_songs_str}"]
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-pro',
                        contents=recommendation_instructions,
                        config=config
                    )
                    
                    new_json_output = extract_json_output(response.text.strip())
                    
                    new_song = new_json_output["songs"]
                    new_reasoning = new_json_output["reasoning"]
                    new_captions = new_json_output["captions"]
                    
                    # Store these songs as previously recommended
                    if "previous_songs" not in st.session_state:
                        st.session_state.previous_songs = []
                    st.session_state.previous_songs.extend(new_song)
                    
                    st.subheader("YOUR NEW TOP SONG CHOICES! 𝄞⨾𓍢ִ໋")
                    
                    for i in range(len(new_song)):
                        with st.expander(f"Recommendation {i+1}: **{new_song[i][0]} by {new_song[i][1]}**", expanded=True):
                            st.markdown(f"**Album:** {new_song[i][2]}")
                            st.markdown(f"**Reasoning:** {new_reasoning[i]}")
                    
                    st.subheader("⊹ ࣪ ˖ Here are some new captions we think you will like ⊹ ࣪ ˖: ")
                    for i, cap in enumerate(new_captions):
                        st.write(f"{i+1}. **{cap}**")

        with col2:
            if st.button("Find songs not on the playlist!"):
                with st.spinner("Searching for new songs..."):
                    config = types.GenerateContentConfig(
                    temperature = 0.4,
                    response_mime_type = "application/json",
                )
                recommendation_instructions = [ f"Please genertate exactly 3 song recommendations ONLY inspired (DO NOT USE DIRECT SONGS) by songs provided from {st.session_state.track_information} for each recommendation provoide a resoning. "
                                        f"Use the description of the post to do a vibe check, check the songs to see which ones best match the users posts description/vibe use {post_description} for this"
                                        f"Generate potential captions also using the description {post_description}"
                                        f"don't repeat any of the songs you already have on the list"
                                        "JSON should include: "
                                        "Each entry in the 'songs' list must be a LIST itself containing [Song Name, Artist Name, Album Name].",
                                        "For example,['Song 1', 'Artist 1', 'Album 1'], ['Song 2', 'Artist 2', 'Album 2']]",
                                        f"1. songs: (list of lists) the top 3 recommendations inspired by the playlist provided that best matches the descristion and vibe of the post"
                                        f"2. reasoning: (list of strings) recommendations reasonings. why should the user pick this song? MATCH WITH SONG ORDER"
                                        f"3. captions: (list of strings) new (DON'T REUSE) captions that a user could use in their instagram/facebook/ other social media post based on descirption"
                                        f"don't use any tracks on the song list provided only use it to help find songs the user might like"
                                        f"only out put in TRUE JSON format"
                                        f"URGENT: don't use any songs from here again {st.session_state.track_information}. Make sure you are not using songs from {st.session_state.track_information}." ]
                response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=recommendation_instructions, 
                config=config                  
                )

                new_json_output = extract_json_output(response.text.strip())

                new_song = new_json_output["songs"]
                new_reasoning = new_json_output["reasoning"]
                new_captions = new_json_output["captions"]

                st.subheader("YOUR NEW TOP SONG CHOICES HAVE BEEN FOUND! 𝄞⨾𓍢ִ໋")

                for i in range(len(new_json_output)):
                    with st.expander(f"Recommendation {i+1}:  **{new_song[i][0]} by {new_song[i][1]}**", expanded = True):
                        st.markdown(f"**Album:** {new_song[i][2]}")
                        st.markdown(f"**Reasoning:** {new_reasoning[i]}")
                        
                    # st.markdown(f"﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌Recommendation {i+1}﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌")
                    # st.markdown(f"╰┈➤Song: {new_song[i][0]}")
                    # st.markdown(f"    ♪Artist: {new_song[i][1]}\n")
                    # st.markdown(f"Reasoning: {new_reasoning[i]} \n")

                st.subheader("⊹ ࣪ ˖ Here are some new captions we think you will like ⊹ ࣪ ˖: ")
                for i, cap in enumerate(new_captions):
                    st.write(f"{i+1}. **{cap}**")

if __name__ == "__main__":
    main()