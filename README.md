
# Music Recommendation System


This project is a web application that helps users discover and create playlists of music based on their preferences. It allows users to identify music, select genres and moods, search for artists, and customize their music recommendations. The application integrates with the Spotify API to fetch music data, including track recommendations, artist information, and genre details.

Users can interact with the application through a user-friendly interface, where they can input their preferences and receive personalized music recommendations. They can also create playlists directly within the application and save them to their Spotify account.

This project is designed for music enthusiasts who want to explore new music, create personalized playlists, and streamline their music discovery process. It caters to users who enjoy discovering music based on specific genres, moods, and artists, offering a convenient platform to curate their music listening experience.



## API Reference

#### Authentication
Authentication with the Spotify API is required for certain endpoints. The application uses OAuth 2.0 for authentication.

Authorization URL
```http
  GET /callback
```
Redirects the user to the Spotify authorization page to grant access to the application.

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `client_id` | `string` | **Required**.  Your client ID. |
| `response_type` | `string` | **Required**. Response type, should be code|
| `redirect_uri` | `string` | **Required**. Redirect URI after authorization|
| `scope` | `string` | **Required**. The requested scopes for user authorization|

#### Genre
  Get Genre List

```http
  GET /genre
```
Returns a list of genres supported by Spotify.

Search Genre
```http
  GET /trial?genre=${genre}
```
Searches for the specified genre and returns artists associated with that genre.
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `genre`      | `string` | **Required**. The genre to search. |

#### Mood
Get Mood Keywords
```http
  GET /mood
```
Returns a list of mood keywords to choose from.

Select Mood Keywords
```http
  POST /select_keywords
```
Selects mood keywords from the provided list.
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `selected_keywords`      | `array` | **Required**.  List of selected mood keywords. |

#### Artist
Search Artist
```http
  GET /search_artist?q=${query}
```
Searches for artists based on the provided query.
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `q`      | `string` | **Required**. The query string. |

Save Selected Artists
```http
  POST /save_selected_artists
```
Saves the selected artists for recommendation.
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `artists`      | `array` | **Required**. List of selected artists. |

#### Features
Save Feature Values
```http
  POST /save_values1
```
Saves the selected feature values for recommendation.
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `energy`      | `number` | **Required**. Energy value.|
| `tempo`      | `number` | **Required**. Tempo value.|
| `danceability`      | `number` | **Required**. Danceability value.|
| `acousticness`      | `number` | **Required**. Acousticness value.|
| `loudness`      | `number` | **Required**. Loudness value.|
| `speechiness`      | `number` | **Required**. Speechiness value.|
| `valence`      | `number` | **Required**. Valence value.|
| `instrumentalness`      | `number` | **Required**. Instrumentalness value.|

#### Recommendations

Get Recommendations

```http
  GET /recommendations
```
Returns recommended tracks based on selected artists, genres, and mood.

#### Playback
Save Playlist
```http
  POST /save_playlist
```
Creates a playlist and adds recommended tracks to it.

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `track_ids`      | `array` | **Required**. List of track IDs.|

#### Submit Feedback
```http
  POST /submit_feedback
```
Submits user feedback to improve recommendations.
| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `name`      | `string` | **Required**. User's name.|
| `feedback`      | `string` | **Required**. User's feedback.|

#### Error Handling
If an error occurs during API requests, appropriate error responses will be returned with corresponding status codes and error messages.
## Acknowledgements

 - [Spotify API](https://developer.spotify.com/documentation/web-api)
 - [Spotipy Library](https://spotipy.readthedocs.io/en/2.22.1/)
 - [Shazamio Library](https://pypi.org/project/shazamio/)
 - [Flask Framework](https://flask.palletsprojects.com/en/3.0.x/)
 - [MongoDB](https://www.mongodb.com/)


## Tech Stack

**Client:** HTML/CSS/JavaScript (Frontend Framework),Shazam API 

**Server:** Python (Backend Language),Flask (Web Framework),MongoDB (Database),MongoEngine or PyMongo (MongoDB ORM),Spotipy (Spotify API Wrapper),OAuth 2.0 (Authentication),Asynchronous Programming 


## License

This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/)


## Authors

- [Chirag Ingale](https://github.com/Chirag10071)
- [Gaurav Jadhav](https://github.com/GAURAV-JADHAV-26)

