from flask import Flask, request, redirect, session, render_template, jsonify,json
from spotipy.oauth2 import SpotifyClientCredentials
import requests,base64,spotipy
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = '1b1b24fc94f2465f92cf10b64d1317da'
CLIENT_SECRET = 'c88f8847d6ef4a60b8c7003318867932'
REDIRECT_URI = 'http://127.0.0.1:8080/callback'
SCOPE = 'user-read-email user-read-private'
GENRE_URL = 'https://api.spotify.com/v1/recommendations/available-genre-seeds'
MOOD_URL = 'https://api.spotify.com/v1/browse/categories/mood/playlists'
AUTHORIZE_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'

client_credentials_manager = SpotifyClientCredentials(client_id='1b1b24fc94f2465f92cf10b64d1317da', client_secret='c88f8847d6ef4a60b8c7003318867932')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

mood_keywords = [
    "happy", "sad", "energetic", "relaxing", "uplifting", "chill", "party", "mellow", "romantic",
    "melancholic", "exciting", "calm", "lively", "dreamy", "groovy", "reflective", "aggressive",
    "serene", "peaceful", "joyful", "hopeful", "melancholy", "blissful", "sentimental", "intense",
    "playful", "optimistic", "dramatic", "moody", "soothing", "bittersweet", "dark", "light",
    "inspiring", "nostalgic", "empowering", "whimsical", "ethereal", "triumphant", "mysterious",
    "enigmatic", "pensive", "tranquil", "enthusiastic", "euphoric", "thoughtful", "suspenseful",
    "ecstatic", "brooding"
]
GenAr = {}
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
def do():
    artists = session['selected_artists']
    genres = session['selected_genres']
    moods = session['selected_keywords']
    global GenAr
    find_tracks_for_combinations1(genres, artists, GenAr)
    print("Mood Based Tracks")
    recommend_playlist_by_mood(moods, GenAr)
    return "Recommendations Processed"

def recommend_playlist_by_mood(moods, GenAr):
    for mood in moods:
        playlists = sp.search(q=f'{mood} mood', type='playlist', limit=5)
        recommended_playlists = playlists['playlists']['items']
        
        for playlist in recommended_playlists:
            playlist_id = playlist['id']
            results = sp.playlist_tracks(playlist_id)
            for track in results['items']:
                track_name = track['track']['name']
                artists = ", ".join([artist['name'] for artist in track['track']['artists']])
                print(f"{track_name} - {artists}")
                
                # Store the track in GenAr under the mood key
                GenAr.setdefault(mood, []).append({
                    'name': track_name,
                    'artists': artists,
                    'id': track['track']['id']
                })

def find_tracks_for_combinations1(genres, artists, GenAr, num_tracks=20):
    all_artist_genres = set()
    all_genres = set(genres)
    artists_not_performing_any_genre = []
    genres_performed_by_no_artists = []

    # Iterate through the artists to find their performed genres
    for artist in artists:
        artist_genres = get_artist_genres(artist)
        if not artist_genres:
            artists_not_performing_any_genre.append(artist)
            continue
        all_artist_genres.update(artist_genres)

    # Iterate through the genres to check if any genre is not performed by any artist
    for genre in genres:
        if genre not in all_artist_genres:
            genres_performed_by_no_artists.append(genre)

    # Iterate through each genre and artist to fetch track IDs
    for genre in genres:
        for artist in artists:
            track_ids = fetch_track_ids(genre, artist, num_tracks)
            if track_ids:
                # Store the track IDs in the dictionary GenAr
                GenAr.setdefault('genre_artist_combinations', {}).setdefault(genre, {}).setdefault(artist, []).extend(track_ids)

                # Print the names of the tracks
                for track_id in track_ids:
                    track_name = get_track_name(track_id)
                    print(f"Track Name: {track_name}")

    # Fetch recommendations for genres performed by no artists
    for genre in genres_performed_by_no_artists:
        # Fetch recommendations using sp.recommendations for each genre
        results = sp.recommendations(seed_genres=[genre], limit=10)
        # Store the track IDs in the dictionary GenAr
        print(f"Genre: {genre}")
        GenAr.setdefault('genres_performed_by_no_artists', {}).setdefault(genre, []).extend([track['id'] for track in results['tracks']])

        # Print the names of the tracks (Optional)
        for track in results['tracks']:
            print(f"Track Name: {track['name']}")
def fetch_track_ids(genre, artist, num_tracks=20):
    artist_genres = get_artist_genres(artist)
    if not artist_genres:
        return []
    if genre not in artist_genres:
        return []
    query = f"genre:{genre} artist:{artist}"
    results = sp.search(q=query, type='track', limit=num_tracks)
    track_ids = [track['id'] for track in results['tracks']['items']]
    return track_ids

def get_artist_genres(artist_name):
    if not artist_name:
        return []
    results = sp.search(q=artist_name, type='artist', limit=1)
    if len(results['artists']['items']) == 0:
        return []
    artist_id = results['artists']['items'][0]['id']
    artist_info = sp.artist(artist_id)
    genres = artist_info['genres']
    return genres

def get_track_name(track_id):
    track_info = sp.track(track_id)
    return track_info['name']

def fetch_top_tracks(entities, num_tracks=10):
    top_tracks = []
    for entity in entities:
        top_tracks.extend(fetch_track_ids(entity, "", num_tracks))
    return top_tracks

def print_top_tracks(track_ids):
    for track_id in track_ids:
        track_name = get_track_name(track_id)
        print(f"Track Name: {track_name}")


if __name__ == '__main__':
    app.run(debug=True, port=8080)
