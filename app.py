from credentials import *
from moods import *
app = Flask(__name__)
app.secret_key = os.urandom(24)



@app.route('/about_us')
def about_us():
    # Render the about_us.html template
    return render_template('about_us.html')

@app.route('/about_project')
def about_project():
    # Render the about_project.html template
    return render_template('about_project.html')




def search_genre(genre):
    # Authenticate with Spotify API
    client_credentials_manager = SpotifyClientCredentials(client_id=credentials.CLIENT_ID, client_secret=credentials.CLIENT_SECRET)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # Search for artists associated with the given genre
    results = sp.search(q='genre:"{}*"'.format(genre), type='artist')
    
    # Check if any artists were found
    if results['artists']['total'] > 0:
        genres = []
        for artist in results['artists']['items']:
            for g in artist['genres']:
                if g.startswith(genre):
                    genres.append({'name': g, 'image': artist.get('images')[0]['url']})  # Add genre name and image URL to the list
        return genres
    else:
        return []  # Return an empty list if no artists were found



class recommendations():
 def get_track_recommendations(title, artist):
    # Search for the track
    results = sp.search(q=f'track:{title} artist:{artist}', type='track', limit=1)
    if(len(results['tracks']['items']) == 0): #error handling 
        results = sp.search(q=artist, type='artist', limit=1)  
        artist_id = results['artists']['items'][0]['id']
        recommendations1 = sp.recommendations(seed_artists=[artist_id], limit=20)
        track_ids = [track['id'] for track in recommendations1['tracks']]
        return track_ids
    # Extract track ID
    track_id = results['tracks']['items'][0]['id']  # Assuming the first track in the search results

    # Get track recommendations based on the seed track
    recommendations1 = sp.recommendations(seed_tracks=[track_id], limit=20)
    track_ids = [track['id'] for track in recommendations1['tracks']]
    return track_ids
class AudioRecorder:
    @staticmethod
    def record_audio(duration, samplerate=44100, channels=2):
        print("Recording audio...")
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='int16')
        sd.wait()
        return recording, samplerate

    @staticmethod
    def save_audio(recording, filename, samplerate):
        sf.write(filename, recording, samplerate)

async def identify_music(filename):
    print("Identifying music...")
    shazam = shazamio.Shazam()
    # Use recognize instead of recognize_song
    track = await shazam.recognize(filename)
    return track
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
        mood_range = mood_definer.mood_ranges.get(mood, {})
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
        thread = threading.Thread(target=fetch_recommendations_for_mood, args=(mood, genre_batches, databases.collection))
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
            databases.collection.insert_one({'artist': artist_name, 'genre': genre, 'track_data': track_data})
    except Exception as e:
        print(f"Error storing tracks for {artist_name} and {genre}: {str(e)}")


def fetch_and_store_tracks(artist, genre, session_features):
    try:
        track_data = fetch_tracks_for_combination(artist, genre, session_features)
        store_tracks(artist, genre, track_data)
    except Exception as e:
        print(f"Error fetching and storing tracks for {artist} and {genre}: {str(e)}")


def get_access_token():
    url = 'https://accounts.spotify.com/api/token'
    headers = {'Authorization': 'Basic ' + base64.b64encode(f'{credentials.CLIENT_ID}:{credentials.CLIENT_SECRET}'.encode()).decode()}
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
def check_language_availability(genre):
    # Search for top artists in the specified genre
    artists = sp.search(q=f'genre:"{genre}"', type='artist', limit=1)
    return len(artists['artists']['items']) > 0
@app.route('/')
def index():
    auth_url = f'{credentials.AUTHORIZE_URL}?client_id={credentials.CLIENT_ID}&response_type=code&redirect_uri={credentials.REDIRECT_URI}&scope={credentials.SCOPE}'
    return render_template('./index.html', auth_url=auth_url)

@app.route('/callback')
def callback(): 
    code = request.args.get('code')
    auth_code = request.args.get('code')
    token_info = sp_oauth.get_access_token(auth_code)
    session['token_info'] = token_info  # Store token information in session
    
    # Retrieve user's email using Spotify API
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.me()
    user_email = user_info['email']
    session['user_email'] = user_email  # Store user's email in session
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': credentials.REDIRECT_URI,
        'client_id': credentials.CLIENT_ID,
        'client_secret': credentials.CLIENT_SECRET
    }
    response = requests.post(credentials.TOKEN_URL, data=data)
    token_info = response.json()
    
    # Storing access token in session
    session['access_token'] = token_info.get('access_token', None)
    return render_template('selector.html')

@app.route('/music_by_music', methods=['GET', 'POST'])
def music_by_music():
    if request.method == 'POST':
        duration = 10  # Recording duration in seconds
        filename = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name

        recording, samplerate = AudioRecorder.record_audio(duration)
        AudioRecorder.save_audio(recording, filename, samplerate)

        try:
            # Use asyncio.run to await the asynchronous function
            track = asyncio.run(identify_music(filename))
            if track:
                title = track['track']['title']
                artist = track['track']['subtitle']
                os.remove(filename)
                return render_template('result.html', title=title, artist=artist)
            else:
                raise Exception("Track not identified")
        except Exception as e:
            os.remove(filename)
            return render_template('music_by_music.html', error="Could not identify music, Please try again.")

    return render_template('music_by_music.html')
@app.route('/confirm', methods=['POST'])
def confirm():
    confirmation = request.form.get('confirmation')
    if confirmation == 'no':
        return redirect(url_for('music_by_music'))

    # If 'Yes' is clicked, proceed with processing the identified music
    title = request.form.get('title')
    artist = request.form.get('artist')
    recommendations1=recommendations.get_track_recommendations(title, artist)
    # Process the identified music as needed
    track_info_list = []
    for track_id in recommendations1:
        track_info = get_track_info(track_id,session.get('access_token') )
        if track_info:
            track_info_list.append(track_info)
    return render_template('playback.html', tracks=track_info_list)
@app.route('/genre')
def genre():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/')

    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(credentials.GENRE_URL, headers=headers)
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
@app.route('/trial', methods=['POST'])
def handle_trial():
    data = request.json
    if data and 'genre' in data:
        searched_genre = data['genre']
        searched_genre=searched_genre.lower()
        gena=search_genre(searched_genre)
    return gena
@app.route('/mood')
def mood():
    return render_template('mood.html', keywords=mood_definer.mood_keywords)

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
        speechiness = float(request.form['speechiness'])
        valence = float(request.form['valence'])
        instrumentalness = float(request.form['instrumentalness'])
        # Store the values in session variables
        session['energy'] = energy
        session['tempo'] = tempo
        session['danceability'] = danceability
        session['acousticness'] = acousticness
        session['loudness'] = loudness
        session['speechiness'] = speechiness
        session['valence'] = valence
        session['instrumentalness'] = instrumentalness
        return redirect('/recommendations')
    else:
        return 'Invalid request method'
@app.route('/recommendations')
def main():
    selected_artists = session.get('selected_artists', [])
    selected_genres = session.get('selected_genres', [])
    selected_moods = session.get('selected_keywords', [])
    if not selected_artists and not selected_genres and not selected_moods:
        playlists = sp.featured_playlists(limit=5)
        all_track_ids = []
        for playlist in playlists['playlists']['items']:
            playlist_info = {
                'name': playlist['name'],
                'id': playlist['id'],
                'owner': playlist['owner']['id']
            }
            # Get tracks for the playlist
            tracks = sp.playlist_tracks(playlist['id'], limit=5)  # Limiting to 5 tracks per playlist
            playlist_info['track_ids'] = [track['track']['id'] for track in tracks['items']]
            all_track_ids.extend(playlist_info['track_ids'])
        track_info_list = []
        for track_id in all_track_ids:
            track_info = get_track_info(track_id,session.get('access_token') )
            if track_info:
                track_info_list.append(track_info)
        return render_template('playback.html', tracks=track_info_list)
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
    collection_name = databases.db['tracks']
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
    Genre_Artist_Combination = databases.collection.count_documents(query1)
    cursor_query1 = databases.collection.find(query1, {'_id': 0, 'track_data': {'$slice': 22}})
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
    Mood = databases.collection.count_documents(query2)
    cursor_query2 = databases.collection.find(query2, {'_id': 0, 'track_data': {'$slice': 20}})
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
    Artist_only = databases.collection.count_documents(query3)
    cursor_query3 = databases.collection.find(query3, {'_id': 0, 'track_data': {'$slice': 18}})
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
    Genre_only = databases.collection.count_documents(query4)
    cursor_query4 = databases.collection.find(query4, {'_id': 0, 'track_data': {'$slice': 16}})
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
    track_similarity_pairs = list(dict.fromkeys(track_similarity_pairs))
    
    track_info_list = []
    unique_track_info_list = []

    # Set to store track names that have been encountered
    encountered_track_names = set()

    # Iterate over track IDs fetched
    for track_id in track_similarity_pairs:
        # Fetch track information using the track ID
        track_info = get_track_info(track_id, session.get('access_token'))
        
        # Check if track information is available
        if track_info:
            # Extract the track name from the track information
            track_name = track_info.get('name', '')

            # Check if the track name has already been encountered
            if track_name not in encountered_track_names:
                # Add the track name to the set of encountered track names
                encountered_track_names.add(track_name)
                
                # Append the track information to the list of unique tracks
                unique_track_info_list.append(track_info)

    # Render the template with unique track information
    return render_template('playback.html', tracks=unique_track_info_list)

@app.route('/save_playlist', methods=['POST'])
def save_playlist():
    # Retrieve track IDs from the POST request
    track_ids = request.form.getlist('track_ids')
    # Get the user's access token (you need to implement this part)
    access_token = session.get('access_token')
    if access_token:
        # Create the playlist
        playlist_id = create_playlist(access_token)

        if playlist_id:
            # Add tracks to the playlist
            add_tracks_to_playlist(access_token, playlist_id, track_ids)
            print('Playlist saved successfully!')
            return render_template('final.html')
        else:
            return 'Failed to create playlist'
    else:
        return 'Failed to get user access token'
def create_playlist(access_token):
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json',
    }

    data = {
        'name': 'Nirvana Playlist',
        'description': 'This is a playlist created via the Spotify API',
        'public': False  # Change to True if you want the playlist to be public
    }

    response = requests.post('https://api.spotify.com/v1/me/playlists', headers=headers, json=data)

    if response.status_code == 201:
        return response.json()['id']
    else:
        return None

def add_tracks_to_playlist(access_token, playlist_id, track_ids):
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json',
    }

    data = {
        'uris': ['spotify:track:' + track_id for track_id in track_ids]
    }

    response = requests.post(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', headers=headers, json=data)
    databases.client.drop_database('music_db')
    session.clear()
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if request.method == 'POST':
        name = request.form['name']
        
        # Retrieve user's email from session
        if 'user_email' in session:
            email = session['user_email']
        else:
            # Handle the case where email is not available
            email = None
        
        feedback = request.form['feedback'] 

        # Store feedback in MongoDB
        feedback_collection = databases.feedbacks_db['feedbacks']
        feedback_collection.insert_one({'name': name, 'email': email, 'feedback': feedback})
        return render_template('final.html')
        # Send thank you email

if __name__ == '__main__':
    import asyncio
    app.run(debug=True, port=8080)