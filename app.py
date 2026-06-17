from flask import Flask, render_template, request, session, redirect
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

API_KEY = "2b865c73f8b7e313a1919d96ad4c9d69"

# Language mapping
languages = {
    "Telugu": "te",
    "Hindi": "hi",
    "English": "en",
    "Tamil": "ta",
    "Kannada": "kn"
}

# Get all genres from TMDB
def get_genres():
    try:
        url = "https://api.themoviedb.org/3/genre/movie/list"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        params = {
            "api_key": API_KEY
        }

        res = requests.get(url, headers=headers, params=params, timeout=10)
        return res.json().get("genres", [])

    except:
        return []
    # Get all genres from TMDB
# 🔥 ADD THIS BELOW get_genres()
def genre_id_to_name_map():
    genres = get_genres()
    return {g["id"]: g["name"] for g in genres}


# Fetch movies based on filters
def fetch_movies(lang=None, genre=None, year=None):
    url = "https://api.themoviedb.org/3/discover/movie"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    def call_api(params):
        try:
            res = requests.get(url, headers=headers, params=params, timeout=10)
            data = res.json()
            return data.get("results", [])
        except:
            return []

    # ✅ BASE PARAMS
    base_params = {
        "api_key": API_KEY,
        "sort_by": "popularity.desc"
    }

    # 🔥 1. FULL FILTER
    params = base_params.copy()

    if lang:
        params["with_original_language"] = lang
    if genre:
        params["with_genres"] = genre
    if year:
        params["primary_release_year"] = year

    movies = call_api(params)

    # 🔥 2. REMOVE YEAR IF EMPTY
    if not movies and year:
        params.pop("primary_release_year", None)
        movies = call_api(params)

    # 🔥 3. REMOVE GENRE IF EMPTY
    if not movies and genre:
        params.pop("with_genres", None)
        movies = call_api(params)

    # 🔥 4. ONLY LANGUAGE
    if not movies and lang:
        params = base_params.copy()
        params["with_original_language"] = lang
        movies = call_api(params)

    # 🔥 5. FINAL FALLBACK (TELUGU TRENDING)
    if not movies:
        params = {
            "api_key": API_KEY,
            "with_original_language": "te",
            "sort_by": "popularity.desc"
        }
        movies = call_api(params)

    return movies
@app.route('/')
def home():
    lang = request.args.get("language")
    if not lang:
        lang = "te"
    genre = request.args.get("genre")
    year = request.args.get("year")

    movies = fetch_movies(lang, genre, year)
    genres = get_genres()

    # 🔥 Year list (2000 → current year)
    current_year = datetime.now().year
    years = list(range(current_year, 1999, -1))

    # Genre mapping
    genre_map = genre_id_to_name_map()
    for movie in movies:
        movie["genre_names"] = [
            genre_map.get(gid, "Unknown") for gid in movie.get("genre_ids", [])
        ]

    return render_template("index.html",
                           movies=movies,
                           genres=genres,
                           languages=languages,
                           years=years,   # ✅ PASS YEARS
                           selected_lang=lang,
                           selected_genre=genre,
                           selected_year=year)

@app.route('/add_watchlist', methods=['POST'])
def add_watchlist():
    movie = request.form.to_dict()

    if 'watchlist' not in session:
        session['watchlist'] = []

    session['watchlist'].append(movie)
    session.modified = True

    return redirect('/')

@app.route('/watchlist')
def watchlist():
    return render_template("watchlist.html",
                           movies=session.get('watchlist', []))

if __name__ == "__main__":
    app.run(debug=True)