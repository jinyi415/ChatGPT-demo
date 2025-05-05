import requests
import json
import re
import time
import os
from dotenv import load_dotenv

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

SYSTEM_PROMPT = """
Always extract 'user' and 'movie' names precisely, even if they are in possessive or embedded form like "user DCSI" or "DCSI's wishlist".
You are an intelligent assistant that converts natural language movie-related requests into MongoDB-style JSON queries.
- If director is a partial name like "Nolan", assume full name "Christopher Nolan".

Your task:
- Only respond with **valid JSON**, with fields:
  - collection (string)
  - action (one of 'find', 'insert', 'update', 'delete', 'count')
  - query (object)
  - sort (object, optional)
  - limit (integer, optional)
  - data (object, optional; used for insert or update)

Guidelines:
- Interpret 'watchlist' as 'wishlist'.
- Fix simple typos (e.g., 'moviees' -> 'movies', 'watched list' -> 'watched').
- Infer missing fields if obvious from user intent (e.g., 'show all users' implies collection='users', action='find', query={}).
- Never return anything other than the JSON itself.

Examples:

Input: "Top 5 thriller movies after 2020"
Output:
{
  "collection": "movies",
  "action": "find",
  "query": { "genre": "Thriller", "release_year": { "$gt": 2020 } },
  "sort": { "rating": -1 },
  "limit": 5
}

Input: "Alice wants to see Joker"
Output:
{
  "collection": "wishlist",
  "action": "insert",
  "data": { "user": "Alice", "movie": "Joker" }
}

Input: "Jinyi watched Inception and gave 9.5"
Output:
{
  "collection": "watched",
  "action": "insert",
  "data": { "user": "Jinyi", "movie": "Inception", "rating": 9.5 }
}

Input: "Delete all movies"
Output:
{
  "collection": "movies",
  "action": "delete",
  "query": {}
}

Input: "Update rating of Dune to 8.7"
Output:
{
  "collection": "movies",
  "action": "update",
  "query": { "title": "Dune" },
  "data": { "rating": 8.7 }
}

Input: "Show all users"
Output:
{
  "collection": "users",
  "action": "find",
  "query": {}
}

Input: "User DCSI wants to see Joker"
Output:
{
  "collection": "wishlist",
  "action": "insert",
  "data": {
    "user": "DCSI",
    "movie": "Joker"
  }
}

Input: "Add Joker to the wishlist of user Jasper"
Output:
{
  "collection": "wishlist",
  "action": "insert",
  "data": {
    "user": "Jasper",
    "movie": "Joker"
  }
}

Input: "Add Joker to DCSI's wishlist"
Output:
{
  "collection": "wishlist",
  "action": "insert",
  "data": {
    "user": "DCSI",
    "movie": "Joker"
  }
}
Input: "Update Jasper's age to 1"
Output:
{
  "collection": "users",
  "action": "update",
  "query": {
    "username": "Jasper"
  },
  "data": {
    "age": 1
  }
}
"""


def call_chatgpt(prompt, max_retries=3):
    print(f"\n🧐 [ChatGPT] Interpreting: {prompt}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    body = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.2
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(OPENAI_API_URL, headers=HEADERS, json=body, timeout=30)
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]

                # 用正则提取 JSON 内容
                match = re.search(r"\{.*\}", content, re.DOTALL)
                if match:
                    content = match.group(0)
                    return json.loads(content)
                else:
                    print("⚠️ No valid JSON found in ChatGPT response.")
                    return {}
            else:
                print(f"❌ ChatGPT API Error [{response.status_code}]: {response.text}")
        except Exception as e:
            print(f"⚠️ ChatGPT request failed on attempt {attempt + 1}: {e}")
            time.sleep(1)  # 简单 retry 间隔

    print("❌ ChatGPT API failed after retries.")
    return {}
