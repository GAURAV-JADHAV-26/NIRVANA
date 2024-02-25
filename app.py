from flask import Flask, request, redirect, session, render_template, jsonify
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime
import requests,base64,spotipy
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = '81508673df21418787b14db997dd2936'
CLIENT_SECRET = '96291925d7ec454e888a4254e5bd2808'
REDIRECT_URI = 'http://127.0.0.1:8080/callback'
SCOPE = 'user-read-email user-read-private'
GENRE_URL = 'https://api.spotify.com/v1/recommendations/available-genre-seeds'
MOOD_URL = 'https://api.spotify.com/v1/browse/categories/mood/playlists'
AUTHORIZE_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'

client_credentials_manager = SpotifyClientCredentials(client_id='81508673df21418787b14db997dd2936', client_secret='96291925d7ec454e888a4254e5bd2808')
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

now = datetime.now()
current_hour = now.hour
time_segment = ""

if 6 <= current_hour < 12:
    time_segment = "morning"
elif 12 <= current_hour < 18:
    time_segment = "afternoon"
elif 18 <= current_hour < 22:
    time_segment = "evening"
else:
    time_segment = "night"

attributes = {
    "morning": {"energy": [0.7, 1.0], "tempo": [100, 150], "danceability": [0.5, 1.0],
                "acousticness": [0.0, 0.5], "loudness": [-20, -5], "instrumentalness": [0.0, 0.3]},
    "afternoon": {"energy": [0.6, 0.8], "tempo": [90, 120], "danceability": [0.4, 0.8],
                  "acousticness": [0.0, 0.5], "loudness": [-20, -5], "instrumentalness": [0.0, 0.3]},
    "evening": {"energy": [0.4, 0.7], "tempo": [60, 100], "danceability": [0.3, 0.6],
                "acousticness": [0.0, 0.5], "loudness": [-20, -5], "instrumentalness": [0.0, 0.3]},
    "night": {"energy": [0.2, 0.5], "tempo": [30, 90], "danceability": [0.2, 0.5],
              "acousticness": [0.0, 0.5], "loudness": [-20, -5], "instrumentalness": [0.0, 0.3]}
}

mood_keywords = [
    "happy", "sad", "energetic", "relaxing", "uplifting", "chill", "party", "mellow", "romantic",
    "melancholic", "exciting", "calm", "lively", "dreamy", "groovy", "reflective", "aggressive",
    "serene", "peaceful", "joyful", "hopeful", "melancholy", "blissful", "sentimental", "intense",
    "playful", "optimistic", "dramatic", "moody", "soothing", "bittersweet", "dark", "light",
    "inspiring", "nostalgic", "empowering", "whimsical", "ethereal", "triumphant", "mysterious",
    "enigmatic", "pensive", "tranquil", "enthusiastic", "euphoric", "thoughtful", "suspenseful",
    "ecstatic", "brooding"
]
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
    return jsonify(success=True)
if __name__ == '__main__':
    app.run(debug=True, port=8080)