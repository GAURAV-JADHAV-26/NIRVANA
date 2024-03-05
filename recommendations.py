def recommend_tracks(num_tracks, num_genres, num_artists, num_moods):
    # Calculate the proportions based on the numbers of genres, artists, and moods
    total = num_genres + num_artists + num_moods
    genre_artist_proportion = (num_genres + num_artists) / total
    mood_proportion = num_moods / total
    
    # Calculate the number of tracks to allocate for genres and artists, and for moods
    num_genre_artist_tracks = int(num_tracks * genre_artist_proportion)
    num_mood_tracks = num_tracks - num_genre_artist_tracks
    print(num_genre_artist_tracks, num_mood_tracks)
    # Generate recommendations based on allocated proportions
    

def generate_genre_artist_recommendations(num_tracks):
    # Logic to generate recommendations based on genres and artists
    pass

def generate_mood_recommendations(num_tracks):
    # Logic to generate recommendations based on moods
    pass

# Example usage:
num_tracks = 100
num_genres = 4
num_artists = 2
num_moods = 5

recommended_tracks = recommend_tracks(num_tracks, num_genres, num_artists, num_moods)
print(recommended_tracks)