from pymongo import MongoClient
from datetime import datetime
import re
from mongo_utils import (
    get_movie_by_title,
    fetch_movies_by_genre_from_tmdb,
    fetch_top_movies_from_tmdb,
    fetch_movies_by_director_from_tmdb,
    search_movies_by_title_tmdb,
    fetch_movies_by_director_flex
)
from GPT_utils import call_chatgpt

client = MongoClient("mongodb://localhost:27017/")
db = client["chatdb"]

def show_user_wishlist(username):
    user = db.users.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})
    if not user:
        print(f"❌ User '{username}' not found.")
        return

    pipeline = [
        {"$match": {"user_id": user["_id"]}},
        {"$lookup": {
            "from": "movies",
            "localField": "movie_id",
            "foreignField": "_id",
            "as": "movie_info"
        }}
    ]
    results = list(db.wishlist.aggregate(pipeline))

    if not results:
        print(f"📭 No wishlist entries found for {username}.")
    else:
        print(f"\n📝 Wishlist for {username}:")
        for entry in results:
            movie_info = entry.get("movie_info", [])
            if not movie_info:
                print(f"\n⚠️ Cannot find movie details for entry: {entry}")
                continue

            movie = movie_info[0]
            print(f"\n🎬 {movie.get('title', 'N/A')} ({movie.get('release_year', 'N/A')})")
            print(f"⭐ Rating: {movie.get('rating', 'N/A')}")
            print(f"📝 Overview: {movie.get('overview', 'N/A')}")


def show_user_watched(username):
    user = db.users.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})
    if not user:
        print(f"❌ User '{username}' not found.")
        return
    pipeline = [
        {"$match": {"user_id": user["_id"]}},
        {"$lookup": {
            "from": "movies",
            "localField": "movie_id",
            "foreignField": "_id",
            "as": "movie_info"
        }}
    ]
    results = list(db.watched.aggregate(pipeline))
    if not results:
        print(f"📭 No watched history found for {username}.")
    else:
        print(f"\n📽️ Watched History for {username}:")
        for entry in results:
            movie_info = entry.get("movie_info", [])
            if not movie_info:
                print(f"\n⚠️ Cannot find movie details for entry: {entry}")
                continue
            movie = movie_info[0]
            print(f"\n🎬 {movie.get('title', 'N/A')} ({movie.get('release_year', 'N/A')})")
            print(f"⭐ Rating: {movie.get('rating', 'N/A')} | Your Score: {entry.get('rating', 'N/A')}")
            print(f"🗓️ Watched on: {entry.get('watched_date', 'N/A')}")


def add_to_wishlist(username, movie_title):
    user = db.users.find_one({"username": re.compile(f"^{re.escape(username)}$", re.IGNORECASE)})
    if not user:
        print("❌ User not found.")
        return

    movie = db.movies.find_one({"title": {"$regex": f"^{movie_title}$", "$options": "i"}})
    if not movie:
        movie = get_movie_by_title(movie_title)
        if not movie:
            print("❌ Movie not found on TMDb either.")
            return

    db.wishlist.insert_one({
        "user_id": user["_id"],
        "movie_id": movie["_id"] if "_id" in movie else db.movies.find_one({"title": movie["title"]})["_id"],
        "added_date": "2025-04-18"
    })
    print(f"✅ Added '{movie_title}' to {username}'s wishlist.")


def add_to_watched(username, movie_title, rating="N/A"):
    user = db.users.find_one({"username": {"$regex": f"^{username}$", "$options": "i"}})
    if not user:
        print("❌ User not found.")
        return

    movie = db.movies.find_one({"title": {"$regex": f"^{movie_title}$", "$options": "i"}})
    if not movie:
        movie = get_movie_by_title(movie_title)
        if not movie:
            print("❌ Movie not found on TMDb either.")
            return

    db.watched.insert_one({
        "user_id": user["_id"],
        "movie_id": movie["_id"] if "_id" in movie else db.movies.find_one({"title": movie["title"]})["_id"],
         "watched_date": datetime.utcnow().isoformat(),
        "rating": rating
    })
    print(f"✅ Added '{movie_title}' to {username}'s watched history.")

def normalize_collection_name(name):
    aliases = {
        "watchlist": "wishlist",
        "watch_list": "wishlist",
        "wish_list": "wishlist",
        "seen": "watched",
        "viewed": "watched",
        "user": "users",
        "movie": "movies",
    }

    if name in db.list_collection_names():
        return name
    elif name in aliases:
        return aliases[name]
    else:
        print(f"\n❌ Collection '{name}' not found.")
        print("📦 Available collections are:")
        for c in db.list_collection_names():
            print(f"🔹 {c}")
        return None


def run_natural_language_query():
    while True:
        prompt = input("\nAsk your question (type 'exit' to quit): ")
        if prompt.lower() in ["exit", "quit"]:
            print("👋 Goodbye!")
            break

        # === NEW: Use CharGOT to interpret all prompts ===
        if "collections" in prompt.lower() and ("show" in prompt.lower() or "list" in prompt.lower()):
            collections = db.list_collection_names()
            print("\n📦 Collections in database:")
            for name in collections:
                print(f"🔹 {name}")
            continue

        result = call_chatgpt(prompt)
        raw_collection = result.get("collection", "movies")
        collection_name = normalize_collection_name(raw_collection)
        if not collection_name:
            continue
        query = result.get("query", {})
        sort = result.get("sort")
        limit = result.get("limit", 5)
        if "all" in prompt.lower():
            limit = 0
        action = result.get("action", "find")

        # Show intent parsing result for demo clarity
        print(f"\n🔍 Interpreted by ChatGPT:")
        print(f"🧾 Action: {action}")
        print(f"📂 Collection: {collection_name}")
        print(f"🧩 Query: {query}")

        # === Custom Hooks for Wishlist/Watched Display ===

        if collection_name == "wishlist" and action == "find" and "user" in query:
            show_user_wishlist(query["user"])
            continue

        if collection_name == "watched" and action == "find" and "user" in query:
            show_user_watched(query["user"])
            continue

        if action == "insert":
            data = result.get("data", {})
            if collection_name == "wishlist" and "user" in data and "movie" in data:
                add_to_wishlist(data["user"], data["movie"])
            elif collection_name == "watched" and "user" in data and "movie" in data:
                rating = data.get("rating", "N/A")
                add_to_watched(data["user"], data["movie"], rating)
            elif data:
                db[collection_name].insert_one(data)
                print(f"✅ Inserted into '{collection_name}': {data}")
            else:
                print("❌ No data provided for insertion.")
            continue

        if action == "update":
            data = result.get("data", {})
            if query and data:
                if collection_name == "watched" and "user" in query and "movie" in query:
                    user = db.users.find_one({"username": {"$regex": f"^{query['user']}$", "$options": "i"}})
                    movie = db.movies.find_one({"title": {"$regex": f"^{query['movie']}$", "$options": "i"}})
                    if user and movie:
                        db.watched.update_one(
                            {"user_id": user["_id"], "movie_id": movie["_id"]},
                            {"$set": data}
                        )
                        print(f"✅ Updated rating for '{query['movie']}' watched by {query['user']}")
                    else:
                        print("❌ User or movie not found.")
                else:
                    db[collection_name].update_one(query, {"$set": data})
                    print(f"✅ Updated '{collection_name}' where {query} with {data}")
            else:
                print("❌ Missing query or data for update.")
            continue

        elif action == "delete":
            if query == {}:
                db[collection_name].delete_many({})
                print(f"✅ Deleted ALL documents in '{collection_name}' collection.")

            elif "user" in query and collection_name in ["wishlist", "watched"]:
                user = db.users.find_one({"username": {"$regex": f"^{query['user']}$", "$options": "i"}})
                if not user:
                    print(f"❌ User {query['user']} not found.")
                    return
                result = db[collection_name].delete_many({"user_id": user["_id"]})
                print(f"✅ Deleted {result.deleted_count} documents from '{collection_name}' for user {query['user']}.")
            elif "user" in query and "movie" in query:
                user = db.users.find_one({"username": {"$regex": f"^{query['user']}$", "$options": "i"}})
                movie = db.movies.find_one({"title": {"$regex": f"^{query['movie']}$", "$options": "i"}})
                if user and movie:
                    db[collection_name].delete_one({"user_id": user["_id"], "movie_id": movie["_id"]})
                    print(f"✅ Deleted {query['movie']} from {query['user']}'s {collection_name}.")
                else:
                    print("❌ User or movie not found.")
            else:
                db[collection_name].delete_one(query)
                print(f"✅ Deleted from '{collection_name}' where {query}")
            continue

        if "collections" in prompt.lower() and ("show" in prompt.lower() or "list" in prompt.lower()):
            collections = db.list_collection_names()
            print("\n📦 Collections in database:")
            for name in collections:
                print(f"🔹 {name}")
            continue

        if action == "count":
            # 🌟 补充 user → user_id 的转换
            if "user" in query and collection_name in ["wishlist", "watched"]:
                user = db.users.find_one({"username": {"$regex": f"^{query['user']}$", "$options": "i"}})
                if not user:
                    print(f"❌ User '{query['user']}' not found.")
                    continue
                query["user_id"] = user["_id"]
                del query["user"]  # 删除原来的 user，避免干扰
            count = db[collection_name].count_documents(query)
            print(f"🔢 Total documents in '{collection_name}' matching {query}: {count}")
            continue

        if action == "find":
            if "title" in query and isinstance(query["title"], str):
                query["title"] = {"$regex": query["title"], "$options": "i"}
            if "director" in query and isinstance(query["director"], str):
                query["director"] = {"$regex": query["director"], "$options": "i"}

            cursor = db[collection_name].find(query)
            if sort:
                for key, direction in sort.items():
                    cursor = cursor.sort(key, direction)
            if limit > 0:
                cursor = cursor.limit(limit)
            found_docs = list(cursor)

            if len(found_docs) < limit and collection_name == "movies" and "title" not in query:
                print("\nFound fewer results than requested. Querying TMDb to supplement...")

                release_gt = None
                release_lt = None
                if "release_year" in query and isinstance(query["release_year"], dict):
                    release_gt = query["release_year"].get("$gt")
                    release_lt = query["release_year"].get("$lt")

                director_name = None
                if "director" in query:
                    director_name = query["director"]
                    if isinstance(director_name, dict):
                        director_name = director_name.get("$regex", "")

                genre_name = None
                if "genre" in query:
                    genre = query["genre"]
                    genre_name = genre.get("$regex") if isinstance(genre, dict) else genre

                inserted = []

                if director_name:
                    from mongo_utils import fetch_movies_by_director_flex
                    inserted = fetch_movies_by_director_flex(
                        director_name=director_name,
                        genre=genre_name,
                        release_year_gt=release_gt,
                        release_year_lt=release_lt,
                        limit=limit - len(found_docs)
                    )
                elif genre_name:
                    from mongo_utils import fetch_movies_by_genre_from_tmdb
                    inserted = fetch_movies_by_genre_from_tmdb(
                        genre_name,
                        limit=limit - len(found_docs),
                        release_year_gt=release_gt,
                        release_year_lt=release_lt
                    )
                else:
                    from mongo_utils import fetch_top_movies_from_tmdb
                    inserted = fetch_top_movies_from_tmdb(
                        limit=limit - len(found_docs),
                        release_year_gt=release_gt,
                        release_year_lt=release_lt
                    )

                if inserted:
                    print(f"🔍 Not enough results in MongoDB. Retrieved from TMDb: {inserted}")
                    cursor = db[collection_name].find(query)
                    if sort:
                        for key, direction in sort.items():
                            cursor = cursor.sort(key, direction)
                    cursor = cursor.limit(limit)
                    found_docs = list(cursor)

            if not found_docs and collection_name == "movies" and "title" in query and "$regex" in query["title"]:
                title_keyword = query["title"]["$regex"]
                print(f"\n📡 Not found locally. Searching TMDb for keyword: '{title_keyword}'")
                inserted_titles = search_movies_by_title_tmdb(title_keyword, limit=5)

                if inserted_titles:
                    print("🔍 Not found in MongoDB. Retrieved from TMDb.")
                    cursor = db[collection_name].find({"title": {"$regex": title_keyword, "$options": "i"}}).limit(5)
                    found_docs = list(cursor)

                    if found_docs:
                        for movie in found_docs:
                            print(f"\n🎬 Title: {movie.get('title', 'N/A')}")
                            print(f"📅 Year: {movie.get('release_year', 'N/A')}")
                            print(f"⭐ Rating: {movie.get('rating', 'N/A')}")
                            print(f"📝 Overview: {movie.get('overview', 'N/A')}")
                            print(f"🎬 Director: {movie.get('director', 'N/A')}")
                            print(f"🎞️ Genre: {movie.get('genre', 'N/A')}")
                        continue

                print("I can't find this movie.")
                continue

            print("\n✅ Found in MongoDB:")
            for doc in found_docs:
                if collection_name == "movies":
                    print(f"\n🎬 Title: {doc.get('title', 'N/A')}")
                    print(f"📅 Year: {doc.get('release_year', 'N/A')}")
                    print(f"⭐ Rating: {doc.get('rating', 'N/A')}")
                    print(f"📝 Overview: {doc.get('overview', 'N/A')}")
                    print(f"🎬 Director: {doc.get('director', 'N/A')}")
                    print(f"🎞️ Genre: {doc.get('genre', 'N/A')}")
                elif collection_name == "users":
                    print(f"\n👤 Username: {doc.get('username', 'N/A')}")
                    print(f"📧 Email: {doc.get('email', 'N/A')}")
                    print(f"🎂 Age: {doc.get('age', 'N/A')}")
                elif collection_name in ["wishlist", "watched"]:
                    print(doc)
                else:
                    print(doc)


if __name__ == "__main__":
    run_natural_language_query()




# Add joker to Jinyi's wishlist
# show jinyi wishlist
# show jinyi's watched history
# show jinyi watched history