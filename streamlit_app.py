"""
Polished UI for product. 
Streamlit is used for User Interface.
"""

import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.exceptions
from google import genai
from google.genai import types
from dotenv import load_dotenv
import json
import sys
import os
import re
import time
import glob
import glob

st.set_page_config(page_title="AI Song & Caption Generatror", page_icon="🎶", layout="centered")

def load_API():
    load_dotenv("spodify.env")
    load_dotenv("gemini.env")

    # Use stable session-level cache path so the same token is reused on reruns
    session_id = st.session_state.get("session_id", "default")
    cache_path = f".cache_{session_id}"
    st.session_state["spotify_cache_path"] = cache_path
    print(f"DEBUG: Using cache path: {cache_path}")

    if os.path.exists(cache_path):
        try:
            cache_size = os.path.getsize(cache_path)
            print(f"DEBUG: Cache file exists, size: {cache_size} bytes")
        except Exception as e:
            print(f"DEBUG: Error checking cache file: {e}")
    else:
        print(f"DEBUG: Cache file does not exist: {cache_path}")

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri="http://127.0.0.1:3000",
        scope="playlist-read-private playlist-read-collaborative",  # Need full permissions for some playlists
        cache_path=cache_path
    ))

    try:
        token_info = sp.auth_manager.get_cached_token()
        if token_info:
            print(f"DEBUG: Found cached token, expires: {token_info.get('expires_at', 'Unknown')}")
            current_time = int(time.time())
            expires_at = token_info.get('expires_at', 0)
            if current_time > expires_at:
                print("DEBUG: Token is expired, refreshing...")
                refresh_token = token_info.get('refresh_token')
                if refresh_token:
                    sp.auth_manager.refresh_access_token(refresh_token)
                else:
                    print("DEBUG: No refresh token available; user must re-authenticate")
        else:
            print("DEBUG: No cached token found")
    except Exception as e:
        print(f"DEBUG: Error checking token: {e}")

    client = genai.Client(api_key=os.getenv("GEMINI_API"))

    return sp, client

def fetch_playlist_ID(url): 
    """Extract playlist ID from Spotify URL with validation"""
    if not url or "spotify.com" not in url or "/playlist/" not in url:
        return None
    try:
        playlist_ID = url.split("/playlist/")[1].split("?")[0]
        if len(playlist_ID) != 22:  # Spotify playlist IDs are 22 characters
            return None
        return playlist_ID
    except:
        return None

def strip_playlist(sp,playlist_ID):
    playlist_songs = []
    skipped_tracks = 0

    # Log current user for debugging
    try:
        current_user = sp.current_user()
        print(f"DEBUG: Current user: {current_user['display_name']} (ID: {current_user['id']})")
    except Exception as e:
        print(f"DEBUG: Could not get current user: {e}")

    # First, try to get basic playlist info to check accessibility
    try:
        playlist_info = sp.playlist(playlist_ID, fields="name,public,owner,collaborative")
        st.info(f"✅ Found playlist: '{playlist_info['name']}' by {playlist_info['owner']['display_name']}")
        st.info(f"Public: {playlist_info['public']}, Collaborative: {playlist_info.get('collaborative', False)}")
        st.info("Attempting to access playlist tracks...")
        print(f"DEBUG: Playlist info retrieved successfully for {playlist_ID}")
    except Exception as e:
        st.error(f"❌ Cannot access playlist info: {str(e)}")
        print(f"DEBUG: Failed to get playlist info for {playlist_ID}: {e}")
        
        # Check if it's a 404 error (playlist doesn't exist)
        if "404" in str(e) or "Resource not found" in str(e):
            st.error("**This playlist URL appears to be invalid or the playlist no longer exists.**")
            st.error("")
            st.error("**Common causes:**")
            st.error("• The playlist URL is outdated or incorrect")
            st.error("• The playlist was deleted by its owner")
            st.error("• The playlist ID in the URL is malformed")
            st.error("")
            st.error("**How to find a working playlist URL:**")
            st.error("1. **Open Spotify app or web player**")
            st.error("2. **Search for the playlist you want** (e.g., 'RapCaviar')")
            st.error("3. **Click 'Share' → 'Copy link to playlist'**")
            st.error("4. **Paste the full URL here**")
            st.error("")
            st.error("**Try these popular, always-working playlists:**")
            st.code("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")  # Today's Top Hits
            st.code("https://open.spotify.com/playlist/37i9dQZF1DX4JAvHpjipBk")  # New Music Friday
            st.code("https://open.spotify.com/playlist/37i9dQZF1DX0XUfEoMdRSg")  # Hot Hits USA
            st.code("https://open.spotify.com/playlist/37i9dQZF1DX48TTZL62Yht")  # RapCaviar (try this!)
            st.error("")
            st.error("**For RapCaviar specifically:**")
            st.error("• Search 'RapCaviar' in Spotify")
            st.error("• Look for the official Spotify playlist")
            st.error("• It should have millions of followers")
            st.info("💡 **Tip:** Spotify playlist URLs change over time. Always copy fresh URLs from the Spotify app!")
        else:
            st.error("**This playlist appears to have special access restrictions**")
            st.error("")
            st.error("**Possible causes:**")
            st.error("• The playlist owner has disabled API access")
            st.error("• The playlist contains content with special licensing")
            st.error("• The playlist is in a private session or has custom restrictions")
            st.error("• Your Spotify app may need additional permissions")
            st.error("")
            st.error("**Try these solutions:**")
            st.error("1. **Ask the playlist owner** to check their playlist settings")
            st.error("2. **Try a different playlist** from the same owner")
            st.error("3. **Use your own playlist** to test if the app works")
            st.error("4. **Check your Spotify app settings** in the developer dashboard")
            st.error("**🎵 Try These Working Examples:**")
            st.error("• **Spotify's Official Playlists** (usually work)")
            st.error("• **Your own playlists** (always work)")
            st.error("• **Recently created public playlists**")
            st.error("• **Playlists from verified artists**")
            st.error("")
            st.code("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M")  # Today's Top Hits
            st.code("https://open.spotify.com/playlist/37i9dQZF1DX4JAvHpjipBk")  # New Music Friday
            st.code("https://open.spotify.com/playlist/37i9dQZF1DX0XUfEoMdRSg")  # Hot Hits USA
            st.error("")
            st.error("**🎯 Most Reliable Option:**")
            st.error("**Create your own playlist!** This will definitely work:")
            st.error("1. Open Spotify app")
            st.error("2. Create new playlist")
            st.error("3. Add 3-5 songs")
            st.error("4. Make it public")
            st.error("5. Copy the URL here")
            st.info("💡 **Note:** Even public playlists can have API restrictions if the owner configures them that way.")
        return []
    
    # Now try to get tracks
    try:
        print(f"DEBUG: Attempting to get tracks for {playlist_ID}")
        results = sp.playlist_tracks(playlist_ID, limit=50)
        print(f"DEBUG: Successfully got tracks")
    except Exception as e:
        st.error(f"❌ Cannot access playlist tracks: {str(e)}")
        print(f"DEBUG: Failed to get tracks for {playlist_ID}: {e}")

        st.error("**This playlist appears to have special access restrictions**")
        st.error("")
        st.error("**Possible causes:**")
        st.error("• The playlist owner has disabled API access")
        st.error("• The playlist contains content with special licensing")
        st.error("• The playlist is in a private session or has custom restrictions")
        st.error("• Your Spotify app may need additional permissions")
        st.error("")
        st.error("**Try this solution:**")
        st.error("**Create your own playlist!** This will definitely work:")
        st.error("1. Open Spotify app")
        st.error("2. Create new playlist")
        st.error("3. Add 3-5 songs")
        st.error("4. Make it public")
        st.error("5. Copy the URL here")
        return []
    
    for item in results['items']:
        track = item.get('track') or item.get('item')
        if track:
            try:
                # Check if track is available
                if track.get('is_local', False):
                    skipped_tracks += 1
                    continue
                    
                # Try to access track details
                song = f"{track['name']}"
                artist = f"{track['artists'][0]['name']}"
                album = f" {track['album']['name']}"

                track_info = [song, artist, album]
                playlist_songs.append(track_info)
            except (KeyError, TypeError, AttributeError) as track_error:
                # Skip tracks with access issues
                skipped_tracks += 1
                continue
    
    # Handle pagination for playlists with more than 50 tracks
    while results.get('next'):
        try:
            results = sp.next(results)
        except Exception as e:
            st.warning(f"⚠️ Could not load additional tracks: {str(e)}")
            break
            
        for item in results['items']:
            track = item.get('track') or item.get('item')
            if track:
                try:
                    # Check if track is available
                    if track.get('is_local', False):
                        skipped_tracks += 1
                        continue
                        
                    # Try to access track details
                    song = f"{track['name']}"
                    artist = f"{track['artists'][0]['name']}"
                    album = f" {track['album']['name']}"

                    track_info = [song, artist, album]
                    playlist_songs.append(track_info)
                except (KeyError, TypeError, AttributeError) as track_error:
                    # Skip tracks with access issues
                    skipped_tracks += 1
                    continue
    
    if skipped_tracks > 0:
        st.warning(f"⚠️ Skipped {skipped_tracks} track(s) due to access issues. Processing {len(playlist_songs)} accessible tracks.")
    
    return playlist_songs

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

    # Initialize session ID for unique caching
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(hash(str(st.session_state) + str(time.time())))[:8]

    sp, client = load_API()

    # Check authentication status
    try:
        user = sp.current_user()
        print(f"DEBUG: Successfully authenticated as: {user['display_name']}")
    except Exception as e:
        print(f"DEBUG: Authentication failed: {e}")
        st.error("❌ **Authentication Required**")
        st.error("You need to authenticate with Spotify to use this app.")
        st.info("**To authenticate:**")
        st.info("1. Click the account management section below")
        st.info("2. Use '🔐 Force Re-Auth' to clear any cached issues")
        st.info("3. Refresh the page and complete Spotify login")
        st.stop()

    st.title("🎶 AI Song & Caption Generator")

    # Account management section
    with st.expander("🔄 Account & Session Management", expanded=False):
        st.markdown("**Having issues with different accounts or playlists?**")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Switch Account", help="Clear cached tokens and authenticate with a different Spotify account"):
                # Clear all cache files
                import glob
                cache_files = glob.glob(".cache*")
                for cache_file in cache_files:
                    try:
                        os.remove(cache_file)
                    except:
                        pass

                # Clear session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]

                st.success("✅ Cache cleared! Please refresh the page and re-authenticate with your new account.")
                st.rerun()

            if st.button("🔐 Force Re-Auth", help="Force complete re-authentication even with existing cache"):
                # Clear current session cache
                cache_path = f".cache_{st.session_state.get('session_id', 'default')}"
                try:
                    if os.path.exists(cache_path):
                        os.remove(cache_path)
                        st.success("✅ Cache cleared for current session!")
                    else:
                        st.info("No cache file found for current session.")
                except Exception as e:
                    st.error(f"Error clearing cache: {e}")

                # Force re-authentication by clearing auth manager
                st.session_state.pop('spotify_auth', None)
                st.info("🔄 Please refresh the page to re-authenticate.")
                st.rerun()

        with col2:
            if st.button("🆕 New Session", help="Start fresh with a new session ID"):
                # Generate new session ID
                st.session_state.session_id = str(hash(str(time.time())))[:8]
                # Clear recommendations but keep track info
                if "recommendations" in st.session_state:
                    del st.session_state.recommendations
                if "previous_songs" in st.session_state:
                    del st.session_state.previous_songs
                st.success("✅ New session started!")
                st.rerun()

        with col3:
            if st.button("🔍 Test Connection", help="Test if Spotify API connection is working"):
                try:
                    user = sp.current_user()
                    st.success(f"✅ Connected to Spotify as: {user['display_name']}")
                    st.info(f"User ID: {user['id']}")
                    st.info(f"Country: {user.get('country', 'Unknown')}")
                    st.info(f"Product: {user.get('product', 'Unknown')}")

                    # Test API access
                    try:
                        playlists = sp.current_user_playlists(limit=1)
                        st.success("✅ API access working - can retrieve playlists")
                    except Exception as api_e:
                        st.warning(f"⚠️ API access issue: {str(api_e)}")

                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
                    st.error("**This usually means:**")
                    st.error("• No authentication token")
                    st.error("• Expired token")
                    st.error("• Invalid app credentials")
                    st.info("**Try:** '🔐 Force Re-Auth' button above, then refresh the page.")

            if st.button("🔧 Debug Cache", help="Check and clean cache files"):
                import glob
                import os
                cache_files = glob.glob(".cache*")
                st.info(f"Found {len(cache_files)} cache files:")
                for cache_file in cache_files:
                    try:
                        file_size = os.path.getsize(cache_file)
                        st.write(f"• {cache_file} ({file_size} bytes)")
                    except:
                        st.write(f"• {cache_file} (size unknown)")

                if st.button("🗑️ Clear All Cache", key="clear_cache_debug"):
                    cleared = 0
                    for cache_file in cache_files:
                        try:
                            os.remove(cache_file)
                            cleared += 1
                        except:
                            pass
                    st.success(f"✅ Cleared {cleared} cache files!")
                    st.rerun()

            if st.button("🔗 Test Playlist Access", help="Test if you can access a specific playlist URL"):
                test_url = st.text_input("Enter playlist URL to test:", key="test_playlist")
                if test_url:
                    test_id = fetch_playlist_ID(test_url)
                    if test_id:
                        st.info(f"🔍 Testing playlist ID: {test_id}")

                        # Step 1: Test basic playlist info access
                        st.write("**Step 1: Testing playlist info access...**")
                        try:
                            playlist_info = sp.playlist(test_id, fields="name,public,owner,collaborative")
                            st.success(f"✅ Playlist info accessible: '{playlist_info['name']}'")
                            st.info(f"Owner: {playlist_info['owner']['display_name']} (ID: {playlist_info['owner']['id']})")
                            st.info(f"Public: {playlist_info['public']}, Collaborative: {playlist_info.get('collaborative', False)}")
                        except Exception as e:
                            st.error(f"❌ Cannot access playlist info: {str(e)}")
                            st.stop()

                        # Step 2: Test track access
                        st.write("**Step 2: Testing track access...**")

                        try:
                            track_results = sp.playlist_tracks(test_id, limit=3)
                            if track_results and track_results['items']:
                                accessible_tracks = 0
                                for item in track_results['items']:
                                    track = item.get('track')
                                    if track and not track.get('is_local', False):
                                        accessible_tracks += 1
                                st.success(f"✅ {accessible_tracks} tracks accessible")
                            else:
                                st.warning("⚠️ No tracks returned")
                        except Exception as e:
                            st.error(f"❌ Track access failed: {str(e)}")

                        # Step 3: Check current user permissions
                        st.write("**Step 3: Checking your account permissions...**")
                        try:
                            user = sp.current_user()
                            st.info(f"Current user: {user['display_name']} (ID: {user['id']})")
                            st.info(f"User country: {user.get('country', 'Unknown')}")
                            st.info(f"User product: {user.get('product', 'Unknown')}")

                            # Check if user owns the playlist
                            playlist_info = sp.playlist(test_id, fields="owner")
                            is_owner = playlist_info['owner']['id'] == user['id']
                            st.info(f"You own this playlist: {is_owner}")

                        except Exception as e:
                            st.error(f"❌ Could not check user info: {str(e)}")

                    else:
                        st.error("❌ Invalid playlist URL format")
    st.markdown("" \
    "**Spodify Playlist Upload:**" \
    "\n   - Needs the **FULL URL** to fetch a playlist." \
    "\n   - Playlist needs to be **public** and less than 100 tracks.")

    provided_playlist = st.text_input("Provide your Public Spotify Playlist URL: ", value=st.session_state.get('selected_playlist_url', ""))

    st.markdown("**Post Information:**\n\n - Give a short description of what your post is about.")
    post_description = st.text_input("Give a short description of what your post is about: ")

    # Add playlist helper section
    with st.expander("🔍 Need Help Finding Playlists?", expanded=False):
        st.markdown("**Can't find the playlist URL you want?**")
            
        st.markdown("**How to get any playlist URL:**")
        st.info("1. Open Spotify (app or web)")
        st.info("2. Find the playlist you want")
        st.info("3. Click the '...' menu → Share → Copy link")
        st.info("4. Paste the full URL above")
        
        st.markdown("**Your Playlists:**")
        if st.button("Load My Playlists", key="load_my_playlists"):
            try:
                playlists = sp.current_user_playlists(limit=10)
                if playlists and playlists['items']:
                    st.success(f"Found {len(playlists['items'])} of your playlists:")
                    for playlist in playlists['items']:
                        if playlist:  # Check if playlist exists
                            name = playlist['name']
                            track_count = playlist.get('tracks', {}).get('total', 0)
                            try:
                                playlist_items = sp.playlist_items(playlist['id'], limit=1)
                                track_count = playlist_items.get('total', track_count)
                            except Exception as e:
                                print(f"DEBUG: Failed to fetch playlist_items for count: {e}")
                            public = "Public" if playlist.get('public', False) else "Private"
                            url = f"https://open.spotify.com/playlist/{playlist['id']}"
                            
                            with st.expander(f"🎵 {name} ({track_count} tracks) - {public}"):
                                st.code(url)
                                if st.button(f"Use This Playlist", key=f"use_{playlist['id']}"):
                                    st.session_state.selected_playlist_url = url
                                    st.success(f"Selected: {name}")
                                    st.rerun()
                else:
                    st.info("You don't have any playlists yet. Create one in Spotify!")
                    st.info("1. Open Spotify app")
                    st.info("2. Click 'Create playlist'")
                    st.info("3. Add some songs")
                    st.info("4. Make it public")
                    st.info("5. Come back here and click 'Load My Playlists'")
            except Exception as e:
                st.error(f"Failed to load your playlists: {str(e)}")
        

    if st.button("Create your Dream Post"):
        if not provided_playlist or not post_description: 
            st.warning("Provide a Public Playlist URL and a post description.")
            st.stop()

        with st.spinner("Fetching tracks..."):
            playlist_ID = fetch_playlist_ID(provided_playlist)
            if not playlist_ID:
                st.error("❌ Invalid playlist URL format. Please provide a valid Spotify playlist URL.")
                st.info("Example: https://open.spotify.com/playlist/4dHFgUF9KFUsed0Qt4cojn")
                st.stop()

            try:
                st.session_state.track_information = strip_playlist(sp, playlist_ID)
                if not st.session_state.track_information:
                    st.error("No tracks found in playlist. Make sure the playlist is public and accessible with your current account.")
                    st.stop()
                st.success(f"Playlist successfully fetched with {len(st.session_state.track_information)} tracks!")
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 403:
                    st.error("❌ Access denied to playlist. This could be because:")
                    st.error("• The playlist contains region-restricted content")
                    st.error("• The playlist is private or has special access restrictions")
                    st.error("• You're using an account from a different region")
                    st.error("• The playlist owner has blocked API access")
                    st.info("💡 Try:")
                    st.info("• Using a different Spotify account")
                    st.info("• Asking the playlist owner to check their settings")
                    st.info("• Using a playlist with globally available tracks")
                elif e.http_status == 404:
                    st.error("❌ Playlist not found. Check that the URL is correct.")
                else:
                    st.error(f"❌ Spotify API error: {e}")
                st.stop()
            except Exception as e:
                st.error(f"❌ Failed to fetch playlist: {e}")
                st.info("💡 If you're having account issues, try the '🔄 Switch Account' button above.")
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