# Refactored mongo_utils.py to extract TMDb insert logic and avoid duplication
import requests
from pymongo import MongoClient

API_KEY = "04c6eb7f6a9360c9b55a669b8d7afa4c"
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_DISCOVER_URL = "https://api.themoviedb.org/3/discover/movie"

GENRE_NAME_TO_ID = {
    "Action": 28,
    "Adventure": 12,
    "Animation": 16,
    "Comedy": 35,
    "Crime": 80,
    "Documentary": 99,
    "Drama": 18,
    "Family": 10751,
    "Fantasy": 14,
    "History": 36,
    "Horror": 27,
    "Music": 10402,
    "Mystery": 9648,
    "Romance": 10749,
    "Science Fiction": 878,
    "TV Movie": 10770,
    "Thriller": 53,
    "War": 10752,
    "Western": 37
}

client = MongoClient("mongodb://localhost:27017/")
db = client["chatdb"]
collection = db["movies"]

def insert_if_not_exists(doc):
    if doc["title"] and doc["release_year"] and not collection.find_one({"title": doc["title"], "release_year": doc["release_year"]}):
        collection.insert_one(doc)
        return True
    return False

def get_movie_by_title(title):
    movie = collection.find_one({"title": title})
    if movie:
        print("\n✅ Found in local MongoDB.")
        return movie

    print("\n📡 Not found locally. Fetching from TMDb...")
    params = {"api_key": API_KEY, "query": title}
    response = requests.get(TMDB_SEARCH_URL, params=params)
    if response.status_code != 200:
        print("TMDb API request failed.")
        return None

    results = response.json().get("results")
    if not results:
        print("No matching movie found on TMDb.")
        return None

    movie = results[0]
    movie_id = movie["id"]

    director = "N/A"
    credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
    credits_response = requests.get(credits_url, params={"api_key": API_KEY})
    if credits_response.status_code == 200:
        crew = credits_response.json().get("crew", [])
        for person in crew:
            if person.get("job") == "Director":
                director = person.get("name")
                break

    genre_ids = movie.get("genre_ids", [])
    genres = [name for name, gid in GENRE_NAME_TO_ID.items() if gid in genre_ids]
    genre = genres[0] if genres else "N/A"

    doc = {
        "title": movie.get("title"),
        "release_year": int(movie["release_date"][:4]) if movie.get("release_date") else None,
        "rating": movie.get("vote_average"),
        "overview": movie.get("overview"),
        "genre": genre,
        "director": director
    }
    if insert_if_not_exists(doc):
        print("💾 Saved to MongoDB.")
    return doc

def fetch_movies_by_genre_from_tmdb(genre, limit=5, release_year_gt=None, release_year_lt=None, release_year_exact=None):
    genre_id = GENRE_NAME_TO_ID.get(genre)
    if not genre_id:
        print(f"⚠️ Genre '{genre}' not recognized.")
        return []

    inserted_titles = []
    page = 1
    collected = 0

    while collected < limit and page <= 5:
        params = {
            "api_key": API_KEY,
            "sort_by": "vote_average.desc",
            "with_genres": genre_id,
            "vote_count.gte": 50,
            "page": page
        }
        if release_year_exact:
            params["primary_release_date.gte"] = f"{release_year_exact}-01-01"
            params["primary_release_date.lte"] = f"{release_year_exact}-12-31"
        else:
            if release_year_gt:
                params["primary_release_date.gte"] = f"{release_year_gt + 1}-01-01"
            if release_year_lt:
                params["primary_release_date.lte"] = f"{release_year_lt}-12-31"

        response = requests.get(TMDB_DISCOVER_URL, params=params)
        if response.status_code != 200:
            print("TMDb discover failed with status code:", response.status_code)
            break

        results = response.json().get("results", [])

        for movie in results:
            if collected >= limit:
                break

            movie_id = movie["id"]

            # 提取导演
            director = "N/A"
            credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
            credits_response = requests.get(credits_url, params={"api_key": API_KEY})
            if credits_response.status_code == 200:
                crew = credits_response.json().get("crew", [])
                for person in crew:
                    if person.get("job") == "Director":
                        director = person.get("name")
                        break

            doc = {
                "title": movie.get("title"),
                "release_year": int(movie["release_date"][:4]) if movie.get("release_date") else None,
                "rating": movie.get("vote_average"),
                "overview": movie.get("overview"),
                "genre": genre,
                "director": director
            }
            if insert_if_not_exists(doc):
                inserted_titles.append(doc["title"])
                collected += 1

        page += 1

    return inserted_titles


def fetch_top_movies_from_tmdb(limit=5, release_year_gt=None, release_year_lt=None, release_year_exact=None):
    inserted_titles = []
    page = 1
    collected = 0

    while collected < limit and page <= 5:
        params = {
            "api_key": API_KEY,
            "sort_by": "vote_average.desc",
            "vote_count.gte": 50,
            "page": page
        }
        if release_year_exact:
            params["primary_release_date.gte"] = f"{release_year_exact}-01-01"
            params["primary_release_date.lte"] = f"{release_year_exact}-12-31"
        else:
            if release_year_gt:
                params["primary_release_date.gte"] = f"{release_year_gt + 1}-01-01"
            if release_year_lt:
                params["primary_release_date.lte"] = f"{release_year_lt}-12-31"

        response = requests.get(TMDB_DISCOVER_URL, params=params)
        if response.status_code != 200:
            print("TMDb discover failed with status code:", response.status_code)
            break

        results = response.json().get("results", [])

        for movie in results:
            if collected >= limit:
                break

            movie_id = movie["id"]

            # 提取导演
            director = "N/A"
            credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
            credits_response = requests.get(credits_url, params={"api_key": API_KEY})
            if credits_response.status_code == 200:
                crew = credits_response.json().get("crew", [])
                for person in crew:
                    if person.get("job") == "Director":
                        director = person.get("name")
                        break

            # 提取 genre
            genre_ids = movie.get("genre_ids", [])
            genre = "N/A"
            for name, gid in GENRE_NAME_TO_ID.items():
                if gid in genre_ids:
                    genre = name
                    break

            doc = {
                "title": movie.get("title"),
                "release_year": int(movie["release_date"][:4]) if movie.get("release_date") else None,
                "rating": movie.get("vote_average"),
                "overview": movie.get("overview"),
                "genre": genre,
                "director": director
            }

            if insert_if_not_exists(doc):
                inserted_titles.append(doc["title"])
                collected += 1

        page += 1

    return inserted_titles

def fetch_movies_by_director_from_tmdb(director_name, limit=5):
    print(f"[INFO] Trying to fetch movies directed by '{director_name}' from TMDb...")

    search_url = "https://api.themoviedb.org/3/search/person"
    params = {"api_key": API_KEY, "query": director_name}
    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        print("❌ Failed to search person.")
        return []

    results = response.json().get("results", [])
    if not results:
        print("❌ No such director found on TMDb.")
        return []

    candidates = [r for r in results if director_name.lower() in r["name"].lower()]
    if not candidates:
        print(f"⚠️ No fuzzy match for '{director_name}' in TMDb person list.")
        return []

    best_match = max(candidates, key=lambda x: x.get("known_for_department") == "Directing" and len(x.get("known_for", [])))

    person_id = best_match["id"]
    true_name = best_match["name"]
    print(f"🎯 Best match: {true_name}")

    credits_url = f"https://api.themoviedb.org/3/person/{person_id}/movie_credits"
    credits_response = requests.get(credits_url, params={"api_key": API_KEY})
    if credits_response.status_code != 200:
        print("❌ Failed to get movie credits.")
        return []

    directed_movies = [m for m in credits_response.json().get("crew", []) if m.get("job") == "Director"]
    sorted_movies = sorted(directed_movies, key=lambda x: x.get("vote_average", 0), reverse=True)

    inserted_titles = []
    for movie in sorted_movies[:limit]:
        genre_ids = movie.get("genre_ids", [])
        genres = [name for name, gid in GENRE_NAME_TO_ID.items() if gid in genre_ids]
        genre = genres[0] if genres else "N/A"

        doc = {
            "title": movie.get("title"),
            "release_year": int(movie["release_date"][:4]) if movie.get("release_date") else None,
            "rating": movie.get("vote_average"),
            "overview": movie.get("overview"),
            "genre": genre,
            "director": true_name
        }

        if insert_if_not_exists(doc):
            inserted_titles.append(doc["title"])
        else:
            print(f"⚠️ Skipped (duplicate?): {doc['title']}")

    return inserted_titles


def search_movies_by_title_tmdb(keyword, limit=5):
    print(f"[TMDb Search] Looking for movies matching: {keyword}")
    params = {"api_key": API_KEY, "query": keyword}
    response = requests.get(TMDB_SEARCH_URL, params=params)
    if response.status_code != 200:
        print("❌ TMDb search request failed.")
        return []

    results = response.json().get("results", [])
    if not results:
        print("❌ No matches found on TMDb.")
        return []

    inserted = []
    for movie in results[:limit]:
        title = movie.get("title")
        release_year = int(movie["release_date"][:4]) if movie.get("release_date") else None
        rating = movie.get("vote_average")
        overview = movie.get("overview")

        movie_id = movie["id"]
        director = "N/A"
        credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
        credits_response = requests.get(credits_url, params={"api_key": API_KEY})
        if credits_response.status_code == 200:
            crew = credits_response.json().get("crew", [])
            for person in crew:
                if person.get("job") == "Director":
                    director = person.get("name")
                    break

        genre_ids = movie.get("genre_ids", [])
        genre_name = "N/A"
        for name, gid in GENRE_NAME_TO_ID.items():
            if gid in genre_ids:
                genre_name = name
                break

        doc = {
            "title": title,
            "release_year": release_year,
            "rating": rating,
            "overview": overview,
            "genre": genre_name,
            "director": director
        }
        if insert_if_not_exists(doc):
            inserted.append(doc["title"])

    return inserted

def fetch_movies_by_director_flex(
    director_name,
    genre=None,
    release_year_gt=None,
    release_year_lt=None,
    limit=5
):
    # Step 1: Resolve genre_id if genre is given
    genre_id = GENRE_NAME_TO_ID.get(genre) if genre else None

    # Step 2: Get director's person ID
    search_url = "https://api.themoviedb.org/3/search/person"
    res = requests.get(search_url, params={"api_key": API_KEY, "query": director_name})
    if res.status_code != 200 or not res.json().get("results"):
        print("❌ Failed to find director on TMDb.")
        return []

    person_id = res.json()["results"][0]["id"]
    true_name = res.json()["results"][0]["name"]
    print(f"🎯 Best match: {true_name}")

    inserted_titles = []
    page = 1
    collected = 0

    while collected < limit and page <= 5:
        discover_url = "https://api.themoviedb.org/3/discover/movie"
        params = {
            "api_key": API_KEY,
            "with_crew": person_id,
            "sort_by": "vote_average.desc",
            "vote_count.gte": 50,
            "page": page
        }

        if genre_id:
            params["with_genres"] = genre_id
        if release_year_gt:
            params["primary_release_date.gte"] = f"{release_year_gt + 1}-01-01"
        if release_year_lt:
            params["primary_release_date.lte"] = f"{release_year_lt}-12-31"

        r = requests.get(discover_url, params=params)
        if r.status_code != 200:
            break
        results = r.json().get("results", [])

        for movie in results:
            if collected >= limit:
                break

            movie_id = movie["id"]
            director = get_director_by_movie_id(movie_id)

            # ✅ 只保留目标导演作品
            if director.lower() != true_name.lower():
                continue

            genre_ids = movie.get("genre_ids", [])
            genres = [name for name, gid in GENRE_NAME_TO_ID.items() if gid in genre_ids]
            genre_name = genres[0] if genres else "N/A"

            doc = {
                "title": movie.get("title"),
                "release_year": int(movie["release_date"][:4]) if movie.get("release_date") else None,
                "rating": movie.get("vote_average"),
                "overview": movie.get("overview"),
                "genre": genre_name,
                "director": director
            }

            if insert_if_not_exists(doc):
                inserted_titles.append(doc["title"])
                collected += 1

        page += 1

    return inserted_titles


def get_director_by_movie_id(movie_id):
    credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits"
    credits_response = requests.get(credits_url, params={"api_key": API_KEY})
    if credits_response.status_code == 200:
        crew = credits_response.json().get("crew", [])
        for person in crew:
            if person.get("job") == "Director":
                return person.get("name")
    return "N/A"
