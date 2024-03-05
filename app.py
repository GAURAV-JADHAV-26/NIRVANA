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
def calculation():
    # Calculate the proportions based on the numbers of genres, artists, and moods
    num_tracks = 100
    num_genres = len(session['selected_genres'])
    num_artists = len(session['selected_artists'])
    num_moods = len(session['selected_keywords'])
    total = num_genres + num_artists + num_moods
    genre_artist_proportion = (num_genres + num_artists) / total
    mood_proportion = num_moods / total
    
    # Calculate the number of tracks to allocate for genres and artists, and for moods
    num_genre_artist_tracks = int(num_tracks * genre_artist_proportion)
    num_mood_tracks = num_tracks - num_genre_artist_tracks
    print(num_genre_artist_tracks, num_mood_tracks)
def track_generation():
    pass
if __name__ == '__main__':
    app.run(debug=True, port=8080)