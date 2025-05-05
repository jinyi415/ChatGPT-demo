# ChatDB: Movie Querying with ChatGPT and MongoDB

This project implements a command-line movie assistant that allows users to interact with a MongoDB movie database using natural language. It leverages ChatGPT (OpenAI API) to interpret user queries, supports full CRUD operations, and integrates with the TMDb API as a fallback data source.

---

## ✨ Key Features

- Natural language interface for querying movie info, watch history, and wishlist
- Uses ChatGPT to parse user intents and convert to structured MongoDB queries
- TMDb API fallback when movie is not found locally
- CLI-based interface with real-time feedback
- Supports `create`, `read`, `update`, `delete` operations on:
  - users
  - movies
  - watch history
  - wishlist
- Export MongoDB collections to `.json` for debugging/demo purposes

---

## 🧰 Tech Stack

- **Python 3.11+**
- **MongoDB** (local)
- **OpenAI GPT (via API)**
- **TMDb API**
- `pymongo`, `openai`, `requests`, `python-dotenv`

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourname/chatdb-movie-assistant.git
cd chatdb-movie-assistant
```

### 2. Set up environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set your API keys in a `.env` file

Create a `.env` file in the root folder:

```
OPENAI_API_KEY=your_openai_key_here
TMDB_API_KEY=your_tmdb_key_here
```

Do **not** commit this file. Use `.env.example` as a reference.

---

## ▶️ Running the Application

```bash
python main.py
```

Then type your questions into the CLI. Examples:

- `show all users`
- `add user Jasper, email jasper@qq.com, age 22`
- `show Jasper's watched history`
- `add Inception to Jinyi's wishlist`
- `update rating of Joker to 9.1 in Jinyi's watched history`
- `delete all movies from Jinyi wishlist`

---

## 🧾 Project Structure

```
.
├── main.py
├── GPT_utils.py
├── mongo_utils.py
├── tmdb_api.py
├── init_collections.py           # Optional: preload database
├── dump_collections.py           # Export all collections to .json
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── data_exports/
    ├── users.json
    ├── movies.json
    ├── watched.json
    └── wishlist.json
```

---

## 🧠 Sample Output(interpreted and answered by ChatGPT)

```bash
Ask your question: show jinyi's wishlist

🎬 Spider-Man: Homecoming (2017)
⭐ Rating: 7.3
📝 Overview: Following the events of Captain America: Civil War...
```

---

## 📦 MongoDB Collection Examples

- `user`:
  ```json
  { "username": "Jinyi", "email": "lashd@qq.com", "age": 10 }
  ```

- `movie`:
  ```json
  { "title": "Interstellar", "year": 2014, "director": "Christopher Nolan", ... }
  ```

- `watched_history`:
  ```json
  { "user": "Jinyi", "movie": "Joker", "score": 8.7, "watched_at": "2025-05-04T21:32:54.667Z" }
  ```

---

## 📌 Notes

- Requires an OpenAI account and TMDb API key.
- Make sure MongoDB is running locally.
- Do **not** commit `.env`; it’s excluded via `.gitignore`.
- Project designed for educational/demo purposes.

---

## 🔐 API Key Setup Guide

This project requires access to two APIs: **OpenAI GPT API** and **TMDb (The Movie Database) API**. You must obtain your own API keys before running the project. This is necessary to keep your credentials secure and avoid exposing personal quotas.

### 1️⃣ OpenAI GPT API Key

- Register at: https://platform.openai.com/signup
- Once logged in, go to [API Keys](https://platform.openai.com/account/api-keys)
- Click "Create new secret key"
- Copy the key (starts with `sk-...`)

### 2️⃣ TMDb API Key

- Register at: https://www.themoviedb.org/
- After logging in, go to [API Settings](https://www.themoviedb.org/settings/api)
- Click “Apply” and choose **Developer** as the usage type
- Fill in some basic info and submit (approval usually takes a few minutes)
- Copy the generated API key (a long hex string)

---

## 📄 Setting Up the `.env` File

Create a file called `.env` in the root project folder (same level as `main.py`).  
Use the following format:

```env
OPENAI_API_KEY=your-openai-api-key-here
TMDB_API_KEY=your-tmdb-api-key-here
```

**Make sure you do not include any spaces or quotes around the values.**

---

## 🛡️ Notes

- Do **not** share your API keys publicly.
- `.env` is ignored by `.gitignore` for safety.
- A sample `.env.example` is provided for reference.
- Both OpenAI and TMDb offer free usage tiers suitable for demos and academic projects.
- This project uses a local MongoDB instance. If you're grading the project and find the database empty, you can use the provided `data_exports/` JSON files to import sample data and test all functionalities locally.


---


## 🧑 Author

Jinyi Wang, USC Spatial Data Science  
Project for DSCI 551 Spring 2025

---
