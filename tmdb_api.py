import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"

def query_tmdb_api(title):
    """
    Search for a movie by title using the TMDb API.

    Args:
        title (str): The title of the movie to search for.

    Returns:
        dict or None: A dictionary containing movie info, or None if not found.
    """
    params = {
        "api_key": API_KEY,
        "query": title
    }

    response = requests.get(TMDB_SEARCH_URL, params=params)

    # Debug output
    # print(f"🔗 Request URL: {response.url}")
    # print(f"📦 Raw Response: {response.json()}")

    if response.status_code != 200:
        print(f"❌ TMDb API request failed with status code: {response.status_code}")
        return None

    results = response.json().get("results")
    if not results:
        print("😢 No matching movie found on TMDb.")
        return None

    movie = results[0]  # Return the first search result
    print(f"🎬 Fetched from TMDb: {movie['title']} ({movie['release_date'][:4]}) - Rating: {movie['vote_average']}")

    return {
        "title": movie["title"],
        "release_year": int(movie["release_date"][:4]) if movie.get("release_date") else 0,
        "rating": movie["vote_average"],
        "overview": movie["overview"],
        "genre": "genre_name "
    }
