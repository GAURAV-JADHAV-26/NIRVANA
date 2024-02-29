from flask import Flask, request, redirect, session, render_template, jsonify,json
from spotipy.oauth2 import SpotifyClientCredentials
import requests,base64,spotipy
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
CLIENT_ID = '1b1b24fc94f2465f92cf10b64d1317da'
CLIENT_SECRET = 'c88f8847d6ef4a60b8c7003318867932'
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
    session['selected_artists'] = request.form.getlist('selected_artists')
    return jsonify(success=True)