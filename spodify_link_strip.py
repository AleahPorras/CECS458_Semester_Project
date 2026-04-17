


import spotipy
from spotipy.oauth2 import SpotifyOAuth
from google import genai
from google.genai import types
import sys 
from dotenv import load_dotenv
import os
import json 
import re

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


def main():
    print("")
    print(f"------------------------------ *Caption and Song Decider* ------------------------------")
    print("Instructions: ")
    print("     Spodify Playlist Uplaod:")
    print("         - Needs the FULL url to fetch a playlist")
    print("         - Playlist needs to be public and less than 100 tracks")
    print("")

    users_playlist = input("Please enter a spodify PUBLIC playlist: ")
    print("Loading...")
    sp = load_API()
    playlist_ID = fetch_playlist_ID(users_playlist)
    try:
        track_info = strip_playlist(sp,playlist_ID)
    except Exception: 
        print()
    print("Playlist fetched sucessfully!")

    post_information = input("Give a short diescription of what your post is about: ")

    print("")
    print("Processing your dream post...")
    print("")

    load_dotenv("gemini.env")
    client = genai.Client(api_key=os.getenv("GEMINI_API"))
    system_instructions = ("You are a trendy music and social media expert that will pick a song from a user that would best fit their description of their post"
                            "Don't use any songs out side of the provided songs unless the user asks for suggestions not on the playlist."
                            "Captions should be gnerated based on the description of the post or music if its relevent to the description"
                            "Format of JSON is top songs you found  are in order and songs are matched with their reasoning in order so that if you turned it into a list it would be indexable so song[0] would be the song to reasoning[0]"
                             "JSON has 3 keys named songs (stores the top 3 song recommendations), reasoning(store matching explenations), and captions(have captions ready for users in case they want them)")
    
    config = types.GenerateContentConfig(
    system_instruction=system_instructions,
    temperature=0.2,
    top_p=0.9,
    top_k=40,
    max_output_tokens=8192,
    response_mime_type="application/json"
    )

    song_recommendation_instructions = [ f"Please genertate exactly 3 song recommendations from the songs provided from {track_info} for each recommendation provoide a resoning "
                                        f"Use the description of the post to do a vibe check, check the songs to see which ones best match the users posts description/vibe use {post_information} for this"
                                        f"Generate potential questions also using the description {post_information}"
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
    
    model_output = response.text.strip()

    try:
        json_data = json.loads(model_output)
        
        
        songs = json_data["songs"]
        reasoning = json_data["reasoning"]
        captions = json_data["captions"]
        
    except json.JSONDecodeError:
        info = response.text.strip()
        #Looking for the json format and taking what is in side (more effective from the other way I was doing it and avoids capturing something that would mess up prints)
        # A more "Bulletproof" fallback
        searching_for_json_object = re.search(r"(\{.*\})", info, re.DOTALL)
        
        #string place holder
        wanted_text = ""
        #checking if we found json
        if searching_for_json_object:
            #takes that group, without json wrap and puts it into wanted text
            wanted_text = searching_for_json_object.group(1) 
        else:
            #due to AI putting out the output chance that AI might not do the wrapper (doubtful tho lol), lastly checks if there was at least somethin returned that resembles json
            if info.startswith("{"):
                    #if found, assigned that to wanted text
                    wanted_text = info
            else:
                #means it didn't find the right format, system exits 
                print("Exiting...")
                sys.exit("AI did not return valid JSON or wasn't found.")
        try:
            #loads into json
            json_data = json.loads(wanted_text)
        except json.JSONDecodeError as e:
            # if user gor here this means our inital check didn't catch this
            print(f"{e}")
            print("Exiting...")
            sys.exit("invalid")

        print(" ")

        songs = json_data["songs"]
        reasoning = json_data["reasoning"]
        captions = json_data["captions"]

        #means that some where there is a mix up, wither wrong number of songs or wrong number of reasoning
        if len(songs) != len(reasoning):
            print("Exiting...")
            sys.exit("Mismatch between number of songs. Google Gemini did not match number of questions with number of reasoning")
 
    print("YOUR TOP SONG CHOICES HAVE BEEN CALCULATED! 𝄞⨾𓍢ִ໋")

    for i in range(len(songs)):
        print(f"﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌Recommendation {i+1}﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌")
        
        print(f"╰┈➤Song: {songs[i][0]}")
        print(f"    ♪Artist: {songs[i][1]}\n")

        print(f"Reasoning: {reasoning[i]} \n")

    print("⊹ ࣪ ˖ Here are some captions we think you will like ⊹ ࣪ ˖: ")

    for i in range(len(captions)):

        print(f"{i+1}. {captions[i]}")
    
    print("")

    found_a_song = input("Were you able to find a song for your post? (yes/no): ")
     
    #error handling in case they didn't answer yes or no
    while found_a_song != 'no' and found_a_song != 'yes':
        print("ERROR: you didn't answer with yes or no (please enter in lower case and as show)")
        #re asks the user
        found_a_song = input("Were you able to find a song for your post? (yes/no): ")
    
    if found_a_song == 'yes': 
        sys.exit("Great! See you later!")
    else: 
        print("")
        print(f"------------------------------ *New Caption and Song Generator* ------------------------------")
        print("")
        generate_rec = input("Would you like us to generate other song recommendations not on the playlist? (yes/no): ")
        #error handling in case they didn't answer yes or no
        while generate_rec != 'no' and generate_rec !='yes':
            print("ERROR: you didn't answer with yes or no (please enter in lower case and as show)")
            #re asks the user
            generate_rec = input("Were you able to find a song for your post? (yes/no): ")

        print("")
        print("Exploring to find new songs...")
        print("")
        
        if generate_rec == 'yes':
            recommendation_instructions = [ f"Please genertate exactly 3 song recommendations ONLY inspired (DO NOT USE DIRECT SONGS) by songs provided from {track_info} for each recommendation provoide a resoning. "
                                        f"Use the description of the post to do a vibe check, check the songs to see which ones best match the users posts description/vibe use {post_information} for this"
                                        f"Generate potential questions also using the description {post_information}"
                                        f"don't repeat any of the songs you already have on the list"
                                        "JSON should include: "
                                        "Each entry in the 'songs' list must be a LIST itself containing [Song Name, Artist Name, Album Name].",
                                        "For example,['Song 1', 'Artist 1', 'Album 1'], ['Song 2', 'Artist 2', 'Album 2']]",
                                        f"1. songs: (list of lists) the top 3 recommendations inspired by the playlist provided that best matches the descristion and vibe of the post"
                                        f"2. reasoning: (list of strings) recommendations reasonings. why should the user pick this song? MATCH WITH SONG ORDER"
                                        f"3. captions: (list of strings) new (DON'T REUSE) captions that a user could use in their instagram/facebook/ other social media post based on descirption"
                                        f"don't use any tracks on the song list provided only use it to help find songs the user might like"
                                        f"only out put in TRUE JASON formate"
                                        f"URGENT: don't use any songs from here again {model_output} make sure that you are not using songs from {track_info} only songs not already recommended or in the playlist can be recommend" ]
            response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=recommendation_instructions, 
            config=config                  
            )
            
            model_output = response.text.strip()

            try:
                json_data = json.loads(model_output)
                
                
                songs = json_data["songs"]
                reasoning = json_data["reasoning"]
                captions = json_data["captions"]
                
            except json.JSONDecodeError:
                info = response.text.strip()
                searching_for_json_object = re.search(r"(\{.*\})", info, re.DOTALL)
                
                #string place holder
                wanted_text = ""
                #checking if we found json
                if searching_for_json_object:
                    #takes that group, without json wrap and puts it into wanted text
                    wanted_text = searching_for_json_object.group(1) 
                else:
                    #due to AI putting out the output chance that AI might not do the wrapper (doubtful tho lol), lastly checks if there was at least somethin returned that resembles json
                    if info.startswith("{"):
                            #if found, assigned that to wanted text
                            wanted_text = info
                    else:
                        #means it didn't find the right format, system exits 
                        print("Exiting...")
                        sys.exit("AI did not return valid JSON or wasn't found.")
                try:
                    #loads into json
                    json_data = json.loads(wanted_text)
                except json.JSONDecodeError as e:
                    # if user gor here this means our inital check didn't catch this
                    print(f"{e}")
                    print("Exiting...")
                    sys.exit("invalid")

                print(" ")

                songs = json_data["songs"]
                reasoning = json_data["reasoning"]
                captions = json_data["captions"]

                #means that some where there is a mix up, wither wrong number of songs or wrong number of reasoning
                if len(songs) != len(reasoning):
                    print("Exiting...")
                    sys.exit("Mismatch between number of songs. Google Gemini did not match number of questions with number of reasoning")
        
            print("YOUR TOP SONG CHOICES HAVE BEEN FOUND! 𝄞⨾𓍢ִ໋")

            for i in range(len(songs)):
                print(f"﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌Recommendation {i+1}﹌﹌﹌﹌﹌﹌﹌﹌﹌﹌")
                
                print(f"╰┈➤Song: {songs[i][0]}")
                print(f"    ♪Artist: {songs[i][1]}\n")

                print(f"Reasoning: {reasoning[i]} \n")

            print("⊹ ࣪ ˖ Here are some captions we think you will like ⊹ ࣪ ˖: ")

            for i in range(len(captions)):

                print(f"{i+1}. {captions[i]}")
            print("")

main()



