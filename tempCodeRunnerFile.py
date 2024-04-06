import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Set up your Spotify API credentials
client_id = '1b1b24fc94f2465f92cf10b64d1317da'
client_secret = 'c88f8847d6ef4a60b8c7003318867932'

# Initialize Spotipy with your credentials
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Function to get the most popular playlists with tracks
def get_most_popular_playlists_with_tracks(limit=10):
    # Get playlists with a limit of 10 (you can adjust the limit as per your requirement)
    playlists = sp.featured_playlists(limit=limit)
    
    # Extract relevant information
    popular_playlists = []
    all_track_ids = []  # Variable to store all track IDs
    for playlist in playlists['playlists']['items']:
        playlist_info = {
            'name': playlist['name'],
            'id': playlist['id'],
            'owner': playlist['owner']['id']
        }
        # Get tracks for the playlist
        tracks = sp.playlist_tracks(playlist['id'], limit=5)  # Limiting to 5 tracks per playlist
        playlist_info['track_ids'] = [track['track']['id'] for track in tracks['items']]
        all_track_ids.extend(playlist_info['track_ids'])  # Append track IDs to the all_track_ids list
        popular_playlists.append(playlist_info)
    return popular_playlists, all_track_ids

# Main function to run the code
def main():
    # Get the most popular playlists with tracks and track IDs
    popular_playlists, all_track_ids = get_most_popular_playlists_with_tracks()

    # Print the results
    print("Most Popular Playlists:")
    for idx, playlist in enumerate(popular_playlists, 1):
        print(f"{idx}. {playlist['name']} by {playlist['owner']}")
        print("   Track IDs:")
        for track_idx, track_id in enumerate(playlist['track_ids'], 1):
            print(f"     {track_idx}. {track_id}")

    print("\nAll Track IDs:")
    for idx, track_id in enumerate(all_track_ids, 1):
        print(f"{idx}. {track_id}")

# Run the main function
if __name__ == "__main__":
    main()