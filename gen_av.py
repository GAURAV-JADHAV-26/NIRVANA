import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Set up your Spotify API credentials
client_id = '1b1b24fc94f2465f92cf10b64d1317da'
client_secret = 'c88f8847d6ef4a60b8c7003318867932'

# Initialize the Spotify client
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Define a function to fetch recommended tracks by genres with popularity filters
def fetch_recommendations_by_genre_with_popularity(genres, min_popularity=0, max_popularity=100, limit=50):
    results = sp.recommendations(seed_genres=genres, min_popularity=min_popularity, max_popularity=max_popularity, limit=limit)
    tracks = results['tracks']
    return tracks

# Example: Fetch 10 recommended tracks based on the genres "pop" and "rock" with popularity between 50 and 100
recommended_tracks = fetch_recommendations_by_genre_with_popularity(['pop', 'rock'], min_popularity=0, max_popularity=100, limit=50)

# Print information about the recommended tracks
for i, track in enumerate(recommended_tracks, start=1):
    print("Track {}: {} - {}".format(i, track['name'], track['artists'][0]['name']))

