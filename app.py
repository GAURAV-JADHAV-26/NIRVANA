from flask import Flask, request, redirect, session, render_template, jsonify,json,url_for
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from motor.motor_asyncio import AsyncIOMotorClient
import requests,base64,spotipy
import pymongo
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import threading
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['music_db']
collection = db['tracks']

CLIENT_ID = '1b1b24fc94f2465f92cf10b64d1317da'
CLIENT_SECRET = 'c88f8847d6ef4a60b8c7003318867932'
REDIRECT_URI = 'http://127.0.0.1:8080/callback'
SCOPE = 'user-read-email user-read-private playlist-modify-public playlist-modify-private'
GENRE_URL = 'https://api.spotify.com/v1/recommendations/available-genre-seeds'
MOOD_URL = 'https://api.spotify.com/v1/browse/categories/mood/playlists'
AUTHORIZE_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
client_credentials_manager = SpotifyClientCredentials(client_id='1b1b24fc94f2465f92cf10b64d1317da', client_secret='c88f8847d6ef4a60b8c7003318867932')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
sp_oauth = SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, scope=SCOPE)
def get_track_info(track_id, access_token):
    headers = {
        'Authorization': 'Bearer ' + access_token
    }
    url = f'https://api.spotify.com/v1/tracks/{track_id}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def fetch_recommendations_for_mood(mood, genre_batches, collection):
    try:
        mood_range = mood_ranges.get(mood, {})
        target_valence = mood_range.get('valence_range', None)
        target_energy = mood_range.get('energy_range', None)
        target_tempo = mood_range.get('tempo_range', None)
        target_danceability = mood_range.get('danceability_range', None)
        target_acousticness = mood_range.get('acousticness_range', None)
        target_loudness = mood_range.get('loudness_range', None)

        track_data = []  # List to store track IDs and features

        for batch_genres in genre_batches:
            recommendations = sp.recommendations(seed_genres=batch_genres,
                                                 target_popularity=100,
                                                 target_valence=target_valence,
                                                 target_energy=target_energy,
                                                 target_tempo=target_tempo,
                                                 target_danceability=target_danceability,
                                                 target_acousticness=target_acousticness,
                                                 target_loudness=target_loudness,
                                                 limit=10)
            for track in recommendations['tracks']:
                track_id = track['id']
                # Fetch track features using Spotify API
                # Append track_id and track_features to track_data list
                track_data.append({'track_id': track_id})

        # Insert mood and track data into collection
        collection.insert_one({'mood': mood, 'track_data': track_data})
    except Exception as e:
        print(f"Error fetching recommendations for mood {mood}: {str(e)}")

def search_tracks_by_sound_features(genres, moods):
    genre_batches = [genres[i:i+5] for i in range(0, len(genres), 5)]
    threads = []

    for mood in moods:
        thread = threading.Thread(target=fetch_recommendations_for_mood, args=(mood, genre_batches, collection))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return 'Tracks stored in MongoDB'

# Get track IDs based on selected genres, moods, and artists
def fetch_and_store_tracks_thread(artist, genre, session_features):
    try:
        track_data = fetch_tracks_for_combination(artist, genre, session_features)
        store_tracks(artist, genre, track_data)
    except Exception as e:
        print(f"Error fetching and storing tracks for {artist} and {genre}: {str(e)}")  
def fetch_top_tracks_for_genre(genre,session_features, limit=10):
    try:
        # Set the target popularity
        target_popularity = 100

        # Get recommendations based on the genre and target popularity
        recommendations_params = {'seed_genres': [genre], 'limit': limit, 'target_popularity': target_popularity}
        recommendations = sp.recommendations(**recommendations_params)

        # Extract track IDs and features
        track_data = []
        for track in recommendations['tracks']:
            track_id = track['id']
            # Fetch track features using Spotify API
            track_features = sp.audio_features(track_id)
            # Calculate cosine similarity with session features
            if track_features:
                # Extract features from session
                # Extract features from track
                track_features = [
                    track_features[0]['energy'],
                    track_features[0]['tempo'],
                    track_features[0]['danceability'],
                    track_features[0]['acousticness'],
                    track_features[0]['loudness'],
                    track_features[0]['speechiness'],
                    track_features[0]['valence'],
                    track_features[0]['instrumentalness']
                ]
                # Calculate cosine similarity
                similarity = cosine_similarity([session_features], [track_features])[0][0]
            else:
                similarity = None
            
            # Add track_id, track_features, and similarity to the track_data list
            track_data.append({'track_id': track_id,'similarity': similarity})
        
        return track_data
    except KeyError as ke:
        print(f"KeyError: {ke}")
        return []
    except Exception as e:
        print(f"Error fetching top tracks for genre {genre}: {str(e)}")
        return []
def fetch_top_track_ids(artist,session_features,limit=10):
    try:
        # Search for the artist
        results = sp.search(q=artist, type='artist', limit=10)
        
        if 'artists' in results and 'items' in results['artists'] and results['artists']['items']:
            # Get the artist's ID
            artist_id = results['artists']['items'][0]['id']
            
            # Fetch the artist's top tracks (limit set to 50)
            top_tracks = sp.artist_top_tracks(artist_id)
            
            # Extract the track IDs and features
            track_data = []
            for track in top_tracks['tracks']:
                track_id = track['id']
                # Fetch track features using Spotify API
                track_features = sp.audio_features(track_id)
                # Add track_id and track_features to the track_data list
                if track_features:
                # Extract features from session
                # Extract features from track
                    track_features = [
                        track_features[0]['energy'],
                        track_features[0]['tempo'],
                        track_features[0]['danceability'],
                        track_features[0]['acousticness'],
                        track_features[0]['loudness'],
                        track_features[0]['speechiness'],
                        track_features[0]['valence'],
                        track_features[0]['instrumentalness']
                    ]
                # Calculate cosine similarity
                    similarity = cosine_similarity([session_features], [track_features])[0][0]
                else:
                    similarity = None
            
            # Add track_id, track_features, and similarity to the track_data list
                track_data.append({'track_id': track_id,'similarity': similarity})
            
            return track_data
        else:
            print(f"No artist found with the name {artist}")
            return []
    except Exception as e:
        print(f"Error fetching top tracks for artist {artist}: {str(e)}")
        return []

def fetch_tracks_for_combination(artist_name, genre,session_features, limit=20):
    try:
        results = sp.search(q=f'artist:{artist_name} genre:{genre}', type='track', limit=limit)
        if results.get('tracks'):
            tracks = results['tracks']['items']
            track_data = []  # List to store track data
            for track in tracks:
                track_id = track['id']
                # Fetch track features using Spotify API
                track_features = sp.audio_features(track_id)
                # Add track_id and track_features to the track_data list
                if track_features:
                # Extract features from session
                    
                # Extract features from track
                    track_features = [
                        track_features[0]['energy'],
                        track_features[0]['tempo'],
                        track_features[0]['danceability'],
                        track_features[0]['acousticness'],
                        track_features[0]['loudness'],
                        track_features[0]['speechiness'],
                        track_features[0]['valence'],
                        track_features[0]['instrumentalness']
                    ]
                # Calculate cosine similarity
                    similarity = cosine_similarity([session_features], [track_features])[0][0]
                else:
                    similarity = None
            
            # Add track_id, track_features, and similarity to the track_data list
                track_data.append({'track_id': track_id,'similarity': similarity})
            return track_data
        else:
            print(f"No tracks found for {artist_name} and {genre}")
            return []
    except Exception as e:
        print(f"Error fetching tracks for {artist_name} and {genre}: {str(e)}")
        return []
def fetch_artist_genres(artist_name):
    # Define the Spotify API endpoint for searching artists
    endpoint = 'https://api.spotify.com/v1/search'
    
    # Define the query parameters
    params = {
        'q': artist_name,
        'type': 'artist',
        'limit': 1  # Limit the search to 1 result
    }
    
    # Define the headers with the access token
    headers = {
        'Authorization': f'Bearer {get_access_token()}',  # Replace YOUR_ACCESS_TOKEN with your actual access token
    }

    try:
        # Send a GET request to the Spotify API
        response = requests.get(endpoint, params=params, headers=headers)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            search_results = response.json()
            
            # Extract the artist information from the search results
            artists = search_results.get('artists', {}).get('items', [])
            
            if artists:
                # Get the first artist from the search results
                artist = artists[0]
                
                # Extract the genres from the artist information
                genres = artist.get('genres', [])
                
                return genres
            else:
                print(f"No artist found with the name '{artist_name}'")
                return []
        else:
            # If the request was not successful, print an error message
            print(f"Failed to fetch artist information for '{artist_name}'. Status code: {response.status_code}")
            return []
    except Exception as e:
        # If an exception occurs, print the error message
        print(f"Error fetching artist genres: {e}")
        return []
def store_tracks(artist_name, genre, track_data):
    try:
            collection.insert_one({'artist': artist_name, 'genre': genre, 'track_data': track_data})
    except Exception as e:
        print(f"Error storing tracks for {artist_name} and {genre}: {str(e)}")


def fetch_and_store_tracks(artist, genre, session_features):
    try:
        track_data = fetch_tracks_for_combination(artist, genre, session_features)
        store_tracks(artist, genre, track_data)
    except Exception as e:
        print(f"Error fetching and storing tracks for {artist} and {genre}: {str(e)}")

mood_keywords = [
    "happy", "sad", "energetic", "relaxing", "uplifting", "chill", "party", "mellow", "romantic",
    "melancholic", "exciting", "calm", "lively", "dreamy", "groovy", "reflective", "aggressive",
    "serene", "peaceful", "joyful", "hopeful", "melancholy", "blissful", "sentimental", "intense",
    "playful", "optimistic", "dramatic", "moody", "soothing", "bittersweet", "dark", "light",
    "inspiring", "nostalgic", "empowering", "whimsical", "ethereal", "triumphant", "mysterious",
    "enigmatic", "pensive", "tranquil", "enthusiastic", "euphoric", "thoughtful", "suspenseful",
    "ecstatic", "brooding"
]
mood_ranges = {
    "happy": {"valence_range": (0.6, 1.0), "energy_range": (0.6, 1.0), "tempo_range": (100, 180), "danceability_range": (0.5, 1.0)},
    "sad": {"valence_range": (0.0, 0.4), "energy_range": (0.0, 0.5), "tempo_range": (50, 100), "acousticness_range": (0.6, 1.0)},
    "energetic": {"energy_range": (0.7, 1.0), "tempo_range": (120, 200), "loudness_range": (-10, -4)},
    "relaxing": {"energy_range": (0.2, 0.5), "tempo_range": (50, 100), "acousticness_range": (0.5, 1.0), "loudness_range": (-30, -15)},
    "uplifting": {"valence_range": (0.6, 1.0), "energy_range": (0.5, 1.0), "tempo_range": (100, 160)},
    "chill": {"energy_range": (0.2, 0.5), "tempo_range": (60, 100), "acousticness_range": (0.5, 1.0)},
    "party": {"energy_range": (0.7, 1.0), "tempo_range": (100, 200), "loudness_range": (-10, -4)},
    "mellow": {"energy_range": (0.2, 0.5), "tempo_range": (50, 90), "acousticness_range": (0.6, 1.0), "loudness_range": (-30, -15)},
    "romantic": {"valence_range": (0.5, 0.8), "tempo_range": (60, 100), "acousticness_range": (0.6, 1.0)},
    "melancholic": {"valence_range": (0.0, 0.4), "energy_range": (0.0, 0.5), "tempo_range": (50, 100), "acousticness_range": (0.6, 1.0)},
    "exciting": {"energy_range": (0.7, 1.0), "tempo_range": (150, 220), "loudness_range": (-8, -3)},
    "calm": {"energy_range": (0.2, 0.5), "tempo_range": (40, 90), "acousticness_range": (0.6, 1.0), "loudness_range": (-30, -15)},
    "lively": {"energy_range": (0.6, 1.0), "tempo_range": (100, 150), "loudness_range": (-8, -3)},
    "dreamy": {"valence_range": (0.5, 0.8), "tempo_range": (60, 110), "acousticness_range": (0.6, 1.0)},
    "groovy": {"energy_range": (0.6, 1.0), "tempo_range": (90, 130), "danceability_range": (0.5, 1.0)},
    "reflective": {"valence_range": (0.3, 0.7), "energy_range": (0.2, 0.6), "tempo_range": (50, 100), "acousticness_range": (0.5, 1.0)},
    "aggressive": {"energy_range": (0.7, 1.0), "tempo_range": (100, 180), "loudness_range": (-3, 0)},
    "serene": {"valence_range": (0.4, 0.7), "tempo_range": (40, 80), "acousticness_range": (0.6, 1.0), "loudness_range": (-30, -15)},
    "peaceful": {"valence_range": (0.4, 0.7), "tempo_range": (40, 80), "acousticness_range": (0.6, 1.0), "loudness_range": (-30, -15)},
    "joyful": {"valence_range": (0.7, 1.0), "energy_range": (0.7, 1.0), "tempo_range": (100, 160)},
    "hopeful": {"valence_range": (0.6, 0.9), "energy_range": (0.6, 1.0), "tempo_range": (90, 140)},
    "blissful": {"valence_range": (0.7, 1.0), "energy_range": (0.6, 1.0), "tempo_range": (80, 120)},
    "sentimental": {"valence_range": (0.3, 0.7), "energy_range": (0.2, 0.6), "tempo_range": (50, 90), "acousticness_range": (0.5, 1.0)},
    "intense": {"valence_range": (0.3, 0.7), "energy_range": (0.7, 1.0), "tempo_range": (120, 200), "loudness_range": (-5, 0)},
    "playful": {"valence_range": (0.6, 1.0), "energy_range": (0.6, 1.0), "tempo_range": (100, 160)},
    "optimistic": {"valence_range": (0.6, 1.0), "energy_range": (0.5, 1.0), "tempo_range": (90, 140)},
    "dramatic": {"valence_range": (0.2, 0.6), "energy_range": (0.6, 1.0), "tempo_range": (80, 120)},
    "moody": {"valence_range": (0.2, 0.6), "energy_range": (0.2, 0.6), "tempo_range": (60, 120), "acousticness_range": (0.5, 1.0)},
    "soothing": {"valence_range": (0.4, 0.7), "energy_range": (0.2, 0.5), "tempo_range": (40, 90), "acousticness_range": (0.6, 1.0), "loudness_range": (-30, -15)},
    "bittersweet": {"valence_range": (0.3, 0.7), "energy_range": (0.2, 0.6), "tempo_range": (60, 100)},
    "dark": {"valence_range": (0.0, 0.4), "energy_range": (0.2, 0.6), "tempo_range": (60, 120), "acousticness_range": (0.6, 1.0)},
    "light": {"valence_range": (0.6, 1.0), "energy_range": (0.4, 0.7), "tempo_range": (80, 120)},
    "inspiring": {"valence_range": (0.7, 1.0), "energy_range": (0.7, 1.0), "tempo_range": (100, 160)},
    "nostalgic": {"valence_range": (0.3, 0.7), "energy_range": (0.3, 0.7), "tempo_range": (60, 100), "acousticness_range": (0.5, 1.0)},
    "empowering": {"valence_range": (0.6, 1.0), "energy_range": (0.7, 1.0), "tempo_range": (100, 160)},
    "whimsical": {"valence_range": (0.5, 0.8), "energy_range": (0.5, 0.8), "tempo_range": (80, 120)},
    "ethereal": {"valence_range": (0.4, 0.7), "energy_range": (0.2, 0.5), "tempo_range": (40, 90), "acousticness_range": (0.6, 1.0), "loudness_range": (-30, -15)},
    "triumphant": {"valence_range": (0.7, 1.0), "energy_range": (0.7, 1.0), "tempo_range": (100, 160)},
    "mysterious": {"valence_range": (0.3, 0.7), "energy_range": (0.3, 0.7), "tempo_range": (60, 120), "acousticness_range": (0.5, 1.0)},
    "enigmatic": {"valence_range": (0.3, 0.7), "energy_range": (0.3, 0.7), "tempo_range": (60, 120), "acousticness_range": (0.5, 1.0)},
    "pensive": {"valence_range": (0.3, 0.7), "energy_range": (0.2, 0.5), "tempo_range": (50, 100), "acousticness_range": (0.5, 1.0), "loudness_range": (-30, -15)},
    "tranquil": {"valence_range": (0.4, 0.7), "energy_range": (0.2, 0.5), "tempo_range": (40, 90), "acousticness_range": (0.6, 1.0), "loudness_range": (-30, -15)},
    "enthusiastic": {"valence_range": (0.6, 1.0), "energy_range": (0.7, 1.0), "tempo_range": (100, 160)},
    "euphoric": {"valence_range": (0.7, 1.0), "energy_range": (0.7, 1.0), "tempo_range": (100, 160)},
    "thoughtful": {"valence_range": (0.3, 0.7), "energy_range": (0.2, 0.6), "tempo_range": (50, 100), "acousticness_range": (0.5, 1.0)},
    "suspenseful": {"valence_range": (0.2, 0.6), "energy_range": (0.6, 1.0), "tempo_range": (80, 120)},
    "ecstatic": {"valence_range": (0.7, 1.0), "energy_range": (0.7, 1.0), "tempo_range": (120, 180)},
    "brooding": {"valence_range": (0.2, 0.6), "energy_range": (0.2, 0.6), "tempo_range": (60, 120), "acousticness_range": (0.5, 1.0)}
}
def get_access_token():
    url = 'https://accounts.spotify.com/api/token'
    headers = {'Authorization': 'Basic ' + base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()}
    data = {'grant_type': 'client_credentials'}
    response = requests.post(url, headers=headers, data=data)
    return response.json()['access_token']

def search_artist(query):
    access_token = get_access_token()
    url = f'https://api.spotify.com/v1/search?q={query}&type=artist'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    data = response.json()
    artists = []
    for artist in data['artists']['items']:
        images = artist['images']
        image_url = images[0]['url'] if images else ''  # Use the first image if available
        artists.append({'id': artist['id'], 'name': artist['name'], 'image': image_url})
    return artists

@app.route('/')
def index():
    auth_url = f'{AUTHORIZE_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}'
    return render_template('./index1.html', auth_url=auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    token_info = response.json()
    
    # Storing access token in session
    session['access_token'] = token_info.get('access_token', None)
    return redirect('/genre')
@app.route('/genre')
def genre():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/')

    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(GENRE_URL, headers=headers)
    if response.status_code == 200:
        genres = response.json().get('genres', [])
        # Add image filenames to the genre data
        genre_data = [{'name': genre, 'image': f'genre_images/{genre.replace(" ", "_").lower()}.jpg'} for genre in genres]
        return render_template('genre.html', genres=genre_data)
    else:
        return f"Failed to retrieve genre list from Spotify API: {response.text}"

@app.route('/select_genres', methods=['POST'])
def select_genres():
    selected_genres = request.form.getlist('selected_genres')
    session['selected_genres'] = selected_genres
    return redirect('/mood')
@app.route('/mood')
def mood():
    return render_template('mood.html', keywords=mood_keywords)

@app.route('/select_keywords', methods=['POST'])
def select_keywords():
    selected_keywords = request.form.getlist('selected_keywords')
    session['selected_keywords'] = selected_keywords
    return redirect('/artist')

@app.route('/artist')
def artist():
    return render_template('artist.html')
@app.route('/search_artist')
def search_artist_endpoint():
    query = request.args.get('q', '')
    return jsonify(search_artist(query))

@app.route('/save_selected_artists', methods=['POST'])
def save_selected_artists():
    data = request.json
    session['selected_artists'] = data['artists']
    print(session['selected_artists'])
    return jsonify(success=True)
@app.route('/features')
def connector():
    return render_template('features1.html')
@app.route('/save_values1', methods=['POST'])
def save_values1():
    if request.method == 'POST':
        # Retrieve the values from the POST request
        energy = request.form['energy']
        tempo = request.form['tempo']
        danceability = request.form['danceability']
        acousticness = request.form['acousticness']
        loudness = request.form['loudness']
        
        # Store the values in session variables
        session['energy'] = energy
        session['tempo'] = tempo
        session['danceability'] = danceability
        session['acousticness'] = acousticness
        session['loudness'] = loudness
        return render_template('features2.html')
    else:
        return 'Invalid request method'
@app.route('/save_values2', methods=['POST'])
def save_values2():
    if request.method == 'POST':
        liveliness = float(request.form['liveliness'])
        speechiness = float(request.form['speechiness'])
        valence = float(request.form['valence'])
        instrumentalness = float(request.form['instrumentalness'])

        # Store values in the session
        session['liveliness'] = liveliness
        session['speechiness'] = speechiness
        session['valence'] = valence
        session['instrumentalness'] = instrumentalness
        return redirect('/recommendations')


@app.route('/recommendations')
def main():
    selected_artists = session.get('selected_artists', [])
    selected_genres = session.get('selected_genres', [])
    selected_moods = session.get('selected_keywords', [])
    session_features = [
                        session.get('energy', 0),
                        session.get('tempo', 0),
                        session.get('danceability', 0),
                        session.get('acousticness', 0),
                        session.get('loudness', 0),
                        session.get('speechiness', 0),
                        session.get('valence', 0),
                        session.get('instrumentalness', 0)
                    ]
    artists_performing_none_of_selected_genres = []
    remaining_genres = set(selected_genres)
    threads = []

    # Create a thread pool
    pool = ThreadPoolExecutor(max_workers=10)

    for artist in selected_artists:
        artist_genres = fetch_artist_genres(artist)

        if not artist_genres:
            artists_performing_none_of_selected_genres.append(artist)
            continue

        intersecting_genres = set(artist_genres).intersection(selected_genres)

        if not intersecting_genres:
            artists_performing_none_of_selected_genres.append(artist)
            continue

        remaining_genres -= set(artist_genres)

        for genre in selected_genres:
            if genre in artist_genres:
                # Submit tasks to the thread pool
                task = pool.submit(fetch_and_store_tracks_thread, artist, genre, session_features)
                threads.append(task)

    # Wait for all tasks to complete
    for task in threads:
        task.result()

    for artist in artists_performing_none_of_selected_genres:
        top_tracks = fetch_top_track_ids(artist, session_features)
        store_tracks(artist, None, top_tracks)

    for genre in remaining_genres:
        top_tracks = fetch_top_tracks_for_genre(genre, session_features)
        store_tracks(None, genre, top_tracks)

    
    try1=search_tracks_by_sound_features(selected_genres, selected_moods)
    print('Tracks fetched and stored successfully')
    print('Artists who perform none of the selected genres:', artists_performing_none_of_selected_genres)
    collection_name = db['tracks']
    track_data = list(collection_name.find())

    for entry in track_data:
        track_list = entry['track_data']
    
    # Check if 'similarity' key exists in each track entry before sorting
        for track_entry in track_list:
            if 'similarity' not in track_entry:
                track_entry['similarity'] = 0  # Setting a default similarity value if key is missing
    
        track_list.sort(key=lambda x: x['similarity'], reverse=True)
        collection_name.update_one({'_id': entry['_id']}, {'$set': {'track_data': track_list}})

    track_similarity_pairs = []  # List to store track ID and similarity pairs

    query1 = {
        '_id': {'$exists': True},
        'artist': {'$exists': True, '$ne': None},
        'genre': {'$exists': True, '$ne': None}
    }
    Genre_Artist_Combination = collection.count_documents(query1)
    cursor_query1 = collection.find(query1, {'_id': 0, 'track_data': {'$slice': 5}})
    document_counter = 0

    # Iterate over documents
    for document in cursor_query1:
        # Increment document counter
        document_counter += 1
        
        # Iterate over track data in the document
        for track_data in document.get('track_data', []):
            # Append track ID and similarity as a tuple to the list
            track_similarity_pairs.append((track_data['track_id'], track_data.get('similarity', 'N/A')))
        
        # If we have fetched 5 tracks from each document, break the loop
        if document_counter == Genre_Artist_Combination:
            break

    query2 = {
        '_id': {'$exists': True},
        'mood': {'$exists': True}
    }
    Mood = collection.count_documents(query2)
    cursor_query2 = collection.find(query2, {'_id': 0, 'track_data': {'$slice': 4}})
    document_counter = 0

    for document in cursor_query2:
        # Increment document counter
        document_counter += 1
        
        # Iterate over track data in the document
        for track_data in document.get('track_data', []):
            # Append track ID and similarity as a tuple to the list
            track_similarity_pairs.append((track_data['track_id'], track_data.get('similarity', 'N/A')))
        
        # If we have fetched 4 tracks from each document, break the loop
        if document_counter == Mood:
            break

    query3 = {
        '_id': {'$exists': True},
        'artist': {'$exists': True},
        'genre': None
    }
    Artist_only = collection.count_documents(query3)
    cursor_query3 = collection.find(query3, {'_id': 0, 'track_data': {'$slice': 3}})
    document_counter = 0

    for document in cursor_query3:
        # Increment document counter
        document_counter += 1
        
        # Iterate over track data in the document
        for track_data in document.get('track_data', []):
            # Append track ID and similarity as a tuple to the list
            track_similarity_pairs.append((track_data['track_id'], track_data.get('similarity', 'N/A')))
        
        # If we have fetched 3 tracks from each document, break the loop
        if document_counter == Artist_only:
            break

    query4 = {
        '_id': {'$exists': True},
        'artist': None,
        'genre': {'$exists': True}
    }
    Genre_only = collection.count_documents(query4)
    cursor_query4 = collection.find(query4, {'_id': 0, 'track_data': {'$slice': 2}})
    document_counter = 0

    for document in cursor_query4:
        # Increment document counter
        document_counter += 1
        
        # Iterate over track data in the document
        for track_data in document.get('track_data', []):
            # Append track ID and similarity as a tuple to the list
            track_similarity_pairs.append((track_data['track_id'], track_data.get('similarity', 'N/A')))
        
        # If we have fetched 2 tracks from each document, break the loop
        if document_counter == Genre_only:
            break
    track_similarity_pairs.sort(key=lambda x: x[1], reverse=True)
    track_similarity_pairs = [track_id for track_id, _ in track_similarity_pairs]
    
    track_info_list = []
    for track_id in track_similarity_pairs:
        track_info = get_track_info(track_id,session.get('access_token') )
        if track_info:
            track_info_list.append(track_info)
    return render_template('playback.html', tracks=track_info_list)

@app.route('/save_playlist', methods=['POST'])
def save_playlist():
    track_ids = request.form.getlist('track_ids')
    playlist_name = 'NirvanaPlaylist'
    token_info = session.get('token_info', None)
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.current_user()
    user_id = user_info['id']
    
    playlist = sp.user_playlist_create(user_id, playlist_name, public=True)
    sp.playlist_add_items(playlist['id'], track_ids)
    
    return 'Playlist saved successfully!'

if __name__ == '__main__':
    app.run(debug=True, port=8080)
