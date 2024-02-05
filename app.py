from flask import Flask, request, redirect, session, render_template
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = '81508673df21418787b14db997dd2936'
CLIENT_SECRET = '96291925d7ec454e888a4254e5bd2808'
REDIRECT_URI = 'http://127.0.0.1:8080/callback'
SCOPE = 'user-read-email user-read-private'
GENRE_URL = 'https://api.spotify.com/v1/recommendations/available-genre-seeds'
#Getting list of moods from Spotify
MOOD_URL = 'https://api.spotify.com/v1/browse/categories/mood/playlists'
AUTHORIZE_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'

@app.route('/')
def index():
    auth_url = f'{AUTHORIZE_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}'
    return render_template('index.html', auth_url=auth_url)

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
        return render_template('genre.html', genres=genres)
    else:
        return f"Failed to retrieve genre list from Spotify API: {response.text}"

@app.route('/select_genres', methods=['POST'])
def select_genres():
    selected_genres = request.form.getlist('selected_genres')
    session['selected_genres'] = selected_genres
    return redirect('/mood')
@app.route('/mood')
def mood():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/')
    
    mood_names = []

    headers = {'Authorization': f'Bearer {access_token}'}
    next_url = MOOD_URL
    while next_url:
        response = requests.get(next_url, headers=headers, params={'limit': 50})#Check if it can be randomised so that the next 50 will be different
        if response.status_code == 200:
            data = response.json()
            mood_items = data.get('playlists', {}).get('items', [])
            mood_names.extend([mood['name'] for mood in mood_items])
            next_url = data.get('playlists', {}).get('next')
        else:
            return f"Failed to retrieve mood playlists from Spotify API: {response.text}"

    return render_template('mood.html', mood_names=mood_names)
if __name__ == '__main__':
    app.run(debug=True, port=8080)