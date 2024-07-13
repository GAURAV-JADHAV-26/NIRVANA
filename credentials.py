from libraries_packages import *
class databases:
 client = pymongo.MongoClient('mongodb://localhost:27017/')
 db = client['music_db']
 collection = db['tracks']
 feedbacks_db = client['feedbacks_db']
 feedbacks_collection = feedbacks_db['feedbacks']

class credentials:
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
sp_oauth = SpotifyOAuth(credentials.CLIENT_ID, credentials.CLIENT_SECRET, credentials.REDIRECT_URI, scope=credentials.SCOPE)