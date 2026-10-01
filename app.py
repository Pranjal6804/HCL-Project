import os
import sys
import re
import urllib.request
import urllib.parse
import json
import time
import pickle
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

print("Loading model artifacts from .pkl files...")
try:
    with open(os.path.join(BASE_DIR, "movies_list.pkl"), "rb") as f:
        movies_df = pickle.load(f)
    with open(os.path.join(BASE_DIR, "knn_model.pkl"), "rb") as f:
        knn_model = pickle.load(f)
    with open(os.path.join(BASE_DIR, "tfidf_matrix.pkl"), "rb") as f:
        tfidf_matrix = pickle.load(f)
    with open(os.path.join(BASE_DIR, "tfidf_vectorizer.pkl"), "rb") as f:
        tfidf_vectorizer = pickle.load(f)
        feature_names = tfidf_vectorizer.get_feature_names_out()
    
    # Load collaborative factors if present
    factors_path = os.path.join(BASE_DIR, "collaborative_item_factors.pkl")
    if os.path.exists(factors_path):
        with open(factors_path, "rb") as f:
            collab_factors = pickle.load(f)
        print(f"Loaded collaborative item factors for {len(collab_factors):,} movies.")
    else:
        collab_factors = {}

    print(f"Loaded {len(movies_df):,} movies and TF-IDF vocabulary successfully.")
except Exception as e:
    print(f"Error loading pkl files: {e}", file=sys.stderr)
    movies_df = pd.DataFrame()
    collab_factors = {}
    feature_names = []

# =========================================================
# High-Performance In-Memory Query & Poster Cache
# =========================================================
POSTER_CACHE = {}
QUERY_CACHE = {}
CACHE_TTL_SECONDS = 3600 * 24  # 24 hours

def get_cached_query(key):
    if key in QUERY_CACHE:
        val, ts = QUERY_CACHE[key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            return val
    return None

def set_cached_query(key, val):
    if len(QUERY_CACHE) > 1000:
        # Simple cleanup
        QUERY_CACHE.clear()
    QUERY_CACHE[key] = (val, time.time())

# =========================================================
# Director & Actor Feature Knowledge Base
# =========================================================
DIRECTOR_CAST_KB = {
    "Inception": {"director": "Christopher Nolan", "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page"]},
    "The Dark Knight": {"director": "Christopher Nolan", "cast": ["Christian Bale", "Heath Ledger", "Gary Oldman"]},
    "Interstellar": {"director": "Christopher Nolan", "cast": ["Matthew McConaughey", "Anne Hathaway", "Jessica Chastain"]},
    "The Matrix": {"director": "Lana & Lilly Wachowski", "cast": ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"]},
    "Pulp Fiction": {"director": "Quentin Tarantino", "cast": ["John Travolta", "Uma Thurman", "Samuel L. Jackson"]},
    "Fight Club": {"director": "David Fincher", "cast": ["Brad Pitt", "Edward Norton", "Helena Bonham Carter"]},
    "Forrest Gump": {"director": "Robert Zemeckis", "cast": ["Tom Hanks", "Robin Wright", "Gary Sinise"]},
    "Toy Story": {"director": "John Lasseter", "cast": ["Tom Hanks", "Tim Allen", "Don Rickles"]},
    "Toy Story 2": {"director": "John Lasseter", "cast": ["Tom Hanks", "Tim Allen", "Joan Cusack"]},
    "Toy Story 3": {"director": "Lee Unkrich", "cast": ["Tom Hanks", "Tim Allen", "Ned Beatty"]},
    "Electric Dreams": {"director": "Steve Barron", "cast": ["Lenny Von Dohlen", "Virginia Madsen", "Maxwell Caulfield"]},
    "Electric Heart": {"director": "Scott Little", "cast": ["Indie Ensemble", "Synth Artists"]},
    "Jurassic Park": {"director": "Steven Spielberg", "cast": ["Sam Neill", "Laura Dern", "Jeff Goldblum"]},
    "Goodfellas": {"director": "Martin Scorsese", "cast": ["Robert De Niro", "Ray Liotta", "Joe Pesci"]},
    "The Godfather": {"director": "Francis Ford Coppola", "cast": ["Marlon Brando", "Al Pacino", "James Caan"]},
    "Avatar": {"director": "James Cameron", "cast": ["Sam Worthington", "Zoe Saldana", "Sigourney Weaver"]},
    "Titanic": {"director": "James Cameron", "cast": ["Leonardo DiCaprio", "Kate Winslet", "Billy Zane"]}
}

def get_movie_meta(clean_title):
    for k, v in DIRECTOR_CAST_KB.items():
        if k.lower() in clean_title.lower() or clean_title.lower() in k.lower():
            return v
    return {"director": None, "cast": []}

# =========================================================
# Real Theatrical Poster Resolver
POPULAR_POSTERS_PRESEED = {
    "inception": "https://upload.wikimedia.org/wikipedia/en/2/2e/Inception_%282010%29_theatrical_poster.jpg",
    "the dark knight": "https://upload.wikimedia.org/wikipedia/en/1/1c/The_Dark_Knight_%282008_film%29.jpg",
    "interstellar": "https://upload.wikimedia.org/wikipedia/en/b/bc/Interstellar_film_poster.jpg",
    "the matrix": "https://upload.wikimedia.org/wikipedia/en/d/db/The_Matrix.png",
    "pulp fiction": "https://upload.wikimedia.org/wikipedia/en/3/3b/Pulp_Fiction_%281994%29_poster.jpg",
    "fight club": "https://upload.wikimedia.org/wikipedia/en/f/fc/Fight_Club_poster.jpg",
    "shutter island": "https://upload.wikimedia.org/wikipedia/en/7/76/Shutterislandposter.jpg",
    "donnie darko": "https://upload.wikimedia.org/wikipedia/en/d/db/Donnie_Darko_poster.jpg",
    "the prestige": "https://upload.wikimedia.org/wikipedia/en/d/d2/Prestige_poster.jpg",
    "memento": "https://upload.wikimedia.org/wikipedia/en/c/c7/Memento_poster.jpg",
    "toy story": "https://upload.wikimedia.org/wikipedia/en/1/13/Toy_Story.jpg",
    "toy story 2": "https://upload.wikimedia.org/wikipedia/en/c/c0/Toy_Story_2.jpg",
    "the revenant": "https://upload.wikimedia.org/wikipedia/en/b/b6/The_Revenant_2015_film_poster.jpg",
    "mad max: fury road": "https://upload.wikimedia.org/wikipedia/en/6/6e/Mad_Max_Fury_Road.jpg",
    "avengers: infinity war - part i": "https://upload.wikimedia.org/wikipedia/en/4/4d/Avengers_Infinity_War_poster.jpg",
    "avengers: infinity war": "https://upload.wikimedia.org/wikipedia/en/4/4d/Avengers_Infinity_War_poster.jpg",
    "father of the bride": "https://upload.wikimedia.org/wikipedia/en/f/fd/FatheroftheBride1950.jpg",
    "father of the bride part ii": "https://upload.wikimedia.org/wikipedia/en/e/e1/Father_of_the_bride_part_ii.jpg",
    "forrest gump": "https://upload.wikimedia.org/wikipedia/en/6/67/Forrest_Gump_poster.jpg",
    "goodfellas": "https://upload.wikimedia.org/wikipedia/en/7/7b/Goodfellas.jpg",
    "the godfather": "https://upload.wikimedia.org/wikipedia/en/1/1c/Godfather_ver1.jpg",
    "blade runner": "https://upload.wikimedia.org/wikipedia/en/9/9f/Blade_Runner_%281982_poster%29.png",
    "jurassic park": "https://upload.wikimedia.org/wikipedia/en/e/e7/Jurassic_Park_poster.jpg",
    "avatar": "https://upload.wikimedia.org/wikipedia/en/d/d6/Avatar_%282009_film%29_poster.jpg",
    "electric dreams": "https://upload.wikimedia.org/wikipedia/en/e/ee/EDposter1984.jpg",
    "electric heart": "https://upload.wikimedia.org/wikipedia/en/e/ee/EDposter1984.jpg",
    "the terminator": "https://upload.wikimedia.org/wikipedia/en/7/70/Terminator1984movieposter.jpg",
    "up": "https://upload.wikimedia.org/wikipedia/en/0/05/Up_%282009_film%29.jpg",
    "wall·e": "https://upload.wikimedia.org/wikipedia/en/c/c2/WALL-Eposter.jpg",
    "finding nemo": "https://upload.wikimedia.org/wikipedia/en/2/29/Finding_Nemo.jpg",
    "the lion king": "https://upload.wikimedia.org/wikipedia/en/3/3d/The_Lion_King_poster.jpg"
}

POSTER_BYTES_CACHE = {}

def generate_fallback_svg(title):
    clean = re.sub(r'\s*\(\d{4}\)', '', str(title)).strip()
    words = clean.split()
    line1 = " ".join(words[:3]) if words else "Cinema"
    line2 = " ".join(words[3:6]) if len(words) > 3 else ""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="600" viewBox="0 0 400 600">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0f172a" />
          <stop offset="50%" stop-color="#090d16" />
          <stop offset="100%" stop-color="#020617" />
        </linearGradient>
        <radialGradient id="glow" cx="50%" cy="30%" r="55%">
          <stop offset="0%" stop-color="#00f0ff" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#bg)"/>
      <rect width="100%" height="100%" fill="url(#glow)"/>
      <circle cx="200" cy="210" r="60" fill="#131e33" stroke="#00f0ff" stroke-width="2" opacity="0.85"/>
      <text x="200" y="225" font-family="'Segoe UI', Roboto, sans-serif" font-size="42" text-anchor="middle" fill="#00f0ff">🎬</text>
      <text x="200" y="325" font-family="'Space Grotesk', 'Segoe UI', sans-serif" font-size="22" font-weight="bold" text-anchor="middle" fill="#ffffff">{line1}</text>
      <text x="200" y="358" font-family="'Space Grotesk', 'Segoe UI', sans-serif" font-size="18" font-weight="600" text-anchor="middle" fill="#94a3b8">{line2}</text>
      <text x="200" y="440" font-family="'Segoe UI', sans-serif" font-size="12" font-weight="700" text-anchor="middle" fill="#00f0ff" letter-spacing="3">CINEPULSE CINEMA</text>
    </svg>'''
    return Response(svg, mimetype="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})

def make_poster_endpoint(raw_url, title):
    if raw_url:
        return f"/api/poster-image?url={urllib.parse.quote(raw_url)}&title={urllib.parse.quote(str(title))}"
    return f"/api/poster-image?title={urllib.parse.quote(str(title))}"

def fetch_wiki_poster(title, year=""):
    clean = re.sub(r'\s*\(\d{4}\)', '', str(title)).strip()
    clean_lower = clean.lower()
    
    # Check pre-seeded known theatrical posters
    if clean_lower in POPULAR_POSTERS_PRESEED:
        return POPULAR_POSTERS_PRESEED[clean_lower]

    cache_key = f"{clean}_{year}".lower()
    if cache_key in POSTER_CACHE:
        return POSTER_CACHE[cache_key]

    candidates = []
    if year:
        candidates.append(f"{clean} ({year} film)")
    candidates.extend([f"{clean} (film)", clean, f"{clean} (American film)"])

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }

    for cand in candidates:
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(cand)}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=2.2) as resp:
                raw_img = data.get('originalimage', {}).get('source') or data.get('thumbnail', {}).get('source')
                if raw_img and ('disambiguation' not in data.get('type', '')):
                    clean_img = raw_img.split('?')[0]
                    # If it's a thumbnail URL, convert to original unscaled master
                    if '/thumb/' in clean_img:
                        parts = clean_img.split('/thumb/')
                        sub_parts = parts[1].split('/')
                        if len(sub_parts) > 1:
                            clean_img = parts[0] + '/' + '/'.join(sub_parts[:-1])
                    POSTER_CACHE[cache_key] = clean_img
                    return clean_img
        except Exception:
            continue

    POSTER_CACHE[cache_key] = None
    return None

# =========================================================
# Explainable AI (XAI) Keyword Extraction Engine
# =========================================================
STOP_TERMS = {'film', 'movie', 'scene', 'character', 'characters', 'story', 'plot', '2020', '1995', '1994', '1999', '2008', '2010', '2014'}

def extract_xai_features(idx1, idx2, max_keywords=4):
    """
    Computes element-wise sparse vector overlap and retrieves top shared thematic tags.
    """
    if len(feature_names) == 0:
        return ["Thematic Alignment", "Genre Concordance"]
        
    vec1 = tfidf_matrix[idx1]
    vec2 = tfidf_matrix[idx2]
    
    # Element-wise product
    prod = vec1.multiply(vec2).toarray()[0]
    top_indices = np.argsort(prod)[::-1]
    
    shared = []
    for i in top_indices:
        if prod[i] <= 0:
            break
        word = feature_names[i]
        if word not in STOP_TERMS and len(word) > 2 and word not in shared:
            # Capitalize nicely
            shared.append(word.title())
            if len(shared) >= max_keywords:
                break
                
    if not shared:
        shared = ["Genre Alignment", "Stylistic Tone"]
    return shared

# =========================================================
# API Endpoints
# =========================================================
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "movies_count": len(movies_df),
        "service": "CinePulse Hybrid AI Recommender Engine",
        "xai_enabled": True,
        "hybrid_enabled": len(collab_factors) > 0
    })

@app.route("/api/poster-image", methods=["GET"])
def proxy_poster_image():
    raw_url = request.args.get("url", "").strip()
    title = request.args.get("title", "Movie").strip()
    
    if not raw_url:
        return generate_fallback_svg(title)
        
    if raw_url in POSTER_BYTES_CACHE:
        c_type, data = POSTER_BYTES_CACHE[raw_url]
        return Response(data, mimetype=c_type, headers={"Cache-Control": "public, max-age=86400"})
        
    try:
        req = urllib.request.Request(
            raw_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
            }
        )
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = resp.read()
            c_type = resp.headers.get("Content-Type", "image/jpeg")
            POSTER_BYTES_CACHE[raw_url] = (c_type, data)
            return Response(data, mimetype=c_type, headers={"Cache-Control": "public, max-age=86400"})
    except Exception as e:
        return generate_fallback_svg(title)

@app.route("/search", methods=["GET"])
def search_movies():
    query = request.args.get("q", "").strip()
    if not query or len(query) < 2:
        return jsonify([])

    # Match title or clean_title
    matches = movies_df[
        movies_df['clean_title'].str.contains(query, case=False, na=False) |
        movies_df['title'].str.contains(query, case=False, na=False)
    ].head(8)

    results = []
    for _, row in matches.iterrows():
        meta = get_movie_meta(row['clean_title'])
        results.append({
            "movieId": int(row['movieId']),
            "title": row['title'],
            "clean_title": row['clean_title'],
            "genres": row['genres'],
            "director": meta['director']
        })

    return jsonify(results)

@app.route("/recommend", methods=["GET", "POST"])
def get_recommendations():
    """
    Main Recommendation Endpoint
    Parameters:
      - movie: Title string
      - top_n: Number of recommendations (default 6)
      - mode: 'content' | 'crowd' | 'hybrid' (default 'hybrid')
    """
    t0 = time.time()
    
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        movie_title = data.get("movie", "")
        top_n = int(data.get("top_n", 6))
        mode = data.get("mode", "hybrid").lower()
    else:
        movie_title = request.args.get("movie", "")
        top_n = int(request.args.get("top_n", 6))
        mode = request.args.get("mode", "hybrid").lower()

    if not movie_title:
        return jsonify({"error": "Movie title parameter is required"}), 400

    cache_key = f"{movie_title.lower()}_{top_n}_{mode}"
    cached = get_cached_query(cache_key)
    if cached:
        cached["cached"] = True
        cached["latency_ms"] = round((time.time() - t0) * 1000, 2)
        return jsonify(cached)

    match = movies_df[movies_df['clean_title'].str.contains(movie_title, case=False, na=False)]
    if match.empty:
        match = movies_df[movies_df['title'].str.contains(movie_title, case=False, na=False)]

    if match.empty:
        return jsonify({"error": f"Movie '{movie_title}' not found in database", "recommendations": []}), 404

    target_idx = match.index[0]
    target_row = movies_df.iloc[target_idx]
    target_mid = int(target_row['movieId'])

    # 1. Content-Based Scores via KNN
    search_k = min(top_n * 4, 30)
    distances, indices = knn_model.kneighbors(tfidf_matrix[target_idx], n_neighbors=search_k + 1)
    
    content_scores = {}
    candidate_indices = []
    for i in range(1, len(indices[0])):
        c_idx = indices[0][i]
        c_dist = distances[0][i]
        c_sim = max(0.0, 1.0 - c_dist)
        content_scores[c_idx] = c_sim
        candidate_indices.append(c_idx)

    # 2. Collaborative Crowd Taste Scores via SVD Factors
    target_has_collab = target_mid in collab_factors
    collab_scores = {}
    if target_has_collab:
        t_vec = collab_factors[target_mid]
        for c_idx in candidate_indices:
            c_mid = int(movies_df.iloc[c_idx]['movieId'])
            if c_mid in collab_factors:
                dot_sim = float(np.dot(t_vec, collab_factors[c_mid]))
                collab_scores[c_idx] = max(0.0, (dot_sim + 1.0) / 2.0)  # Map [-1, 1] to [0, 1]
            else:
                collab_scores[c_idx] = content_scores[c_idx]
    else:
        for c_idx in candidate_indices:
            collab_scores[c_idx] = content_scores[c_idx]

    # 3. Mode Blending (Content, Crowd, or True Hybrid)
    ranked_candidates = []
    for c_idx in candidate_indices:
        s_content = content_scores[c_idx]
        s_crowd = collab_scores.get(c_idx, s_content)
        
        if mode == "content":
            final_score = s_content
        elif mode == "crowd":
            final_score = s_crowd
        else:  # hybrid
            final_score = 0.55 * s_content + 0.45 * s_crowd
            
        ranked_candidates.append((c_idx, final_score, s_content, s_crowd))

    ranked_candidates.sort(key=lambda x: x[1], reverse=True)
    top_candidates = ranked_candidates[:top_n]

    # 4. Build Output with Explainable AI & Real Posters
    target_meta = get_movie_meta(target_row['clean_title'])
    recommendations = []
    
    for c_idx, f_score, s_cont, s_crwd in top_candidates:
        rec_row = movies_df.iloc[c_idx]
        year_match = re.search(r'\((\d{4})\)', str(rec_row['title']))
        year = year_match.group(1) if year_match else ""
        
        # Real poster lookup
        raw_poster_url = fetch_wiki_poster(rec_row['clean_title'], year)
        poster_url = make_poster_endpoint(raw_poster_url, rec_row['clean_title'])
        
        # Explainable AI shared tags
        shared_themes = extract_xai_features(target_idx, c_idx)
        rec_meta = get_movie_meta(rec_row['clean_title'])

        # Director match boost note
        if target_meta['director'] and rec_meta['director'] and target_meta['director'] == rec_meta['director']:
            shared_themes.insert(0, f"Directed by {target_meta['director']}")

        match_pct = round(f_score * 100, 1)

        recommendations.append({
            "movieId": int(rec_row['movieId']),
            "title": rec_row['title'],
            "clean_title": rec_row['clean_title'],
            "year": year,
            "genres": rec_row['genres'],
            "director": rec_meta['director'],
            "cast": rec_meta['cast'],
            "poster_url": poster_url,
            "match_score": f"{match_pct}%",
            "score_numeric": match_pct,
            "content_score": f"{round(s_cont*100, 1)}%",
            "crowd_score": f"{round(s_crwd*100, 1)}%",
            "shared_themes": shared_themes,
            "xai_explanation": f"Recommended because both share thematic tags in {', '.join(shared_themes[:3])}."
        })

    # Target poster lookup
    t_year_match = re.search(r'\((\d{4})\)', str(target_row['title']))
    t_year = t_year_match.group(1) if t_year_match else ""
    raw_target_poster = fetch_wiki_poster(target_row['clean_title'], t_year)
    target_poster = make_poster_endpoint(raw_target_poster, target_row['clean_title'])

    response_payload = {
        "query": target_row['title'],
        "clean_query": target_row['clean_title'],
        "genres": target_row['genres'],
        "director": target_meta['director'],
        "cast": target_meta['cast'],
        "target_poster": target_poster,
        "mode": mode,
        "total_recommendations": len(recommendations),
        "recommendations": recommendations,
        "cached": False,
        "latency_ms": round((time.time() - t0) * 1000, 2)
    }

    set_cached_query(cache_key, response_payload)
    return jsonify(response_payload)

# =========================================================
# Curated Category Horizontal Carousels Endpoint
# =========================================================
CATEGORIES_CATALOG = {
    "cult_classics": [
        {"title": "Pulp Fiction (1994)", "year": "1994", "genres": "Comedy|Crime|Drama", "poster": "https://upload.wikimedia.org/wikipedia/en/3/3b/Pulp_Fiction_%281994%29_poster.jpg"},
        {"title": "Fight Club (1999)", "year": "1999", "genres": "Action|Crime|Drama|Thriller", "poster": "https://upload.wikimedia.org/wikipedia/en/f/fc/Fight_Club_poster.jpg"},
        {"title": "The Matrix (1999)", "year": "1999", "genres": "Action|Sci-Fi|Thriller", "poster": "https://upload.wikimedia.org/wikipedia/en/d/db/The_Matrix.png"},
        {"title": "Goodfellas (1990)", "year": "1990", "genres": "Crime|Drama", "poster": "https://upload.wikimedia.org/wikipedia/en/7/7b/Goodfellas.jpg"},
        {"title": "The Godfather (1972)", "year": "1972", "genres": "Crime|Drama", "poster": "https://upload.wikimedia.org/wikipedia/en/1/1c/Godfather_ver1.jpg"},
        {"title": "Forrest Gump (1994)", "year": "1994", "genres": "Comedy|Drama|Romance|War", "poster": "https://upload.wikimedia.org/wikipedia/en/6/67/Forrest_Gump_poster.jpg"}
    ],
    "mind_bending": [
        {"title": "Inception (2010)", "year": "2010", "genres": "Action|Crime|Drama|Mystery|Sci-Fi", "poster": "https://upload.wikimedia.org/wikipedia/en/2/2e/Inception_%282010%29_theatrical_poster.jpg"},
        {"title": "The Prestige (2006)", "year": "2006", "genres": "Drama|Mystery|Sci-Fi|Thriller", "poster": "https://upload.wikimedia.org/wikipedia/en/d/d2/Prestige_poster.jpg"},
        {"title": "Memento (2000)", "year": "2000", "genres": "Mystery|Thriller", "poster": "https://upload.wikimedia.org/wikipedia/en/c/c7/Memento_poster.jpg"},
        {"title": "Shutter Island (2010)", "year": "2010", "genres": "Drama|Mystery|Thriller", "poster": "https://upload.wikimedia.org/wikipedia/en/7/76/Shutterislandposter.jpg"},
        {"title": "Eternal Sunshine (2004)", "year": "2004", "genres": "Drama|Romance|Sci-Fi", "poster": "https://upload.wikimedia.org/wikipedia/en/a/a4/Eternal_Sunshine_of_the_Spotless_Mind.png"},
        {"title": "Donnie Darko (2001)", "year": "2001", "genres": "Drama|Mystery|Sci-Fi", "poster": "https://upload.wikimedia.org/wikipedia/en/d/db/Donnie_Darko_poster.jpg"}
    ],
    "sci_fi": [
        {"title": "Interstellar (2014)", "year": "2014", "genres": "Adventure|Drama|Sci-Fi", "poster": "https://upload.wikimedia.org/wikipedia/en/b/bc/Interstellar_film_poster.jpg"},
        {"title": "Blade Runner (1982)", "year": "1982", "genres": "Action|Sci-Fi|Thriller", "poster": "https://upload.wikimedia.org/wikipedia/en/9/9f/Blade_Runner_%281982_poster%29.png"},
        {"title": "Jurassic Park (1993)", "year": "1993", "genres": "Action|Adventure|Sci-Fi|Thriller", "poster": "https://upload.wikimedia.org/wikipedia/en/e/e7/Jurassic_Park_poster.jpg"},
        {"title": "Avatar (2009)", "year": "2009", "genres": "Action|Adventure|Sci-Fi", "poster": "https://upload.wikimedia.org/wikipedia/en/d/d6/Avatar_%282009_film%29_poster.jpg"},
        {"title": "The Terminator (1984)", "year": "1984", "genres": "Action|Sci-Fi", "poster": "https://upload.wikimedia.org/wikipedia/en/7/70/Terminator1984movieposter.jpg"},
        {"title": "Electric Dreams (1984)", "year": "1984", "genres": "Comedy|Drama|Music|Sci-Fi", "poster": "https://upload.wikimedia.org/wikipedia/en/e/ee/EDposter1984.jpg"}
    ],
    "animated": [
        {"title": "Toy Story (1995)", "year": "1995", "genres": "Adventure|Animation|Children|Comedy|Fantasy", "poster": "https://upload.wikimedia.org/wikipedia/en/1/13/Toy_Story.jpg"},
        {"title": "Toy Story 2 (1999)", "year": "1999", "genres": "Adventure|Animation|Children|Comedy|Fantasy", "poster": "https://upload.wikimedia.org/wikipedia/en/c/c0/Toy_Story_2.jpg"},
        {"title": "Up (2009)", "year": "2009", "genres": "Adventure|Animation|Children|Drama", "poster": "https://upload.wikimedia.org/wikipedia/en/0/05/Up_%282009_film%29.jpg"},
        {"title": "WALL·E (2008)", "year": "2008", "genres": "Adventure|Animation|Children|Romance|Sci-Fi", "poster": "https://upload.wikimedia.org/wikipedia/en/c/c2/WALL-Eposter.jpg"},
        {"title": "Finding Nemo (2003)", "year": "2003", "genres": "Adventure|Animation|Children|Comedy", "poster": "https://upload.wikimedia.org/wikipedia/en/2/29/Finding_Nemo.jpg"},
        {"title": "The Lion King (1994)", "year": "1994", "genres": "Adventure|Animation|Children|Drama|Musical", "poster": "https://upload.wikimedia.org/wikipedia/en/3/3d/The_Lion_King_poster.jpg"}
    ]
}

@app.route("/api/categories", methods=["GET"])
def get_categories():
    formatted = {}
    for cat, items in CATEGORIES_CATALOG.items():
        formatted[cat] = [
            {
                "title": it["title"],
                "year": it.get("year", ""),
                "genres": it.get("genres", ""),
                "poster": make_poster_endpoint(it["poster"], it["title"])
            }
            for it in items
        ]
    return jsonify(formatted)

# =========================================================
# Interactive 5-Star Rating & Live Personal Taste Vector
# =========================================================
@app.route("/api/taste-profile", methods=["POST"])
def get_taste_profile_recommendations():
    """
    Computes a personalized taste vector from user ratings:
    Body: {"ratings": [{"title": "Inception", "rating": 5}, {"title": "The Matrix", "rating": 4.5}]}
    """
    data = request.get_json(silent=True) or {}
    user_ratings = data.get("ratings", [])
    
    if not user_ratings:
        return jsonify({"recommendations": []})

    # Build weighted taste vector: W = sum((rating - 2.5) * vector)
    combined_vector = np.zeros(tfidf_matrix.shape[1], dtype=np.float32)
    rated_indices = set()

    for item in user_ratings:
        title = item.get("title", "")
        rating = float(item.get("rating", 3.0))
        weight = rating - 2.5  # Positive for >= 3 stars, negative for < 2.5
        
        match = movies_df[movies_df['clean_title'].str.contains(title, case=False, na=False)]
        if not match.empty:
            idx = match.index[0]
            rated_indices.add(idx)
            row_vec = tfidf_matrix[idx].toarray()[0]
            combined_vector += weight * row_vec

    norm = np.linalg.norm(combined_vector)
    if norm > 0:
        combined_vector /= norm

    # Matrix dot product
    sims = tfidf_matrix.dot(combined_vector)
    
    # Exclude already rated movies
    for idx in rated_indices:
        sims[idx] = -1.0

    top_indices = np.argsort(sims)[::-1][:6]
    
    recs = []
    for idx in top_indices:
        score = float(sims[idx])
        if score <= 0:
            continue
        row = movies_df.iloc[idx]
        year_match = re.search(r'\((\d{4})\)', str(row['title']))
        year = year_match.group(1) if year_match else ""
        raw_p = fetch_wiki_poster(row['clean_title'], year)
        poster_url = make_poster_endpoint(raw_p, row['clean_title'])
        
        recs.append({
            "movieId": int(row['movieId']),
            "title": row['title'],
            "clean_title": row['clean_title'],
            "year": year,
            "genres": row['genres'],
            "poster_url": poster_url,
            "match_score": f"{round(score * 100, 1)}%",
            "xai_explanation": "Tailored live to your 5-star ratings profile across genre & thematic markers."
        })

    return jsonify({
        "recommendations": recs,
        "rated_count": len(user_ratings)
    })

# =========================================================
# Mood-Based Recommender Filter
# =========================================================
MOOD_MAP = {
    "mind_bending": ["Sci-Fi", "Mystery", "Thriller"],
    "action": ["Action", "Adventure", "Crime"],
    "emotional": ["Drama", "Romance"],
    "late_night": ["Film-Noir", "Crime", "Mystery", "Thriller"]
}

@app.route("/api/mood", methods=["GET"])
def get_mood_movies():
    mood = request.args.get("mood", "mind_bending").lower()
    cache_key = f"mood_{mood}"
    cached = get_cached_query(cache_key)
    if cached:
        return jsonify(cached)

    target_genres = MOOD_MAP.get(mood, ["Sci-Fi", "Thriller"])
    
    # Filter movies containing any target genre
    pattern = "|".join(target_genres)
    subset = movies_df[movies_df['genres'].str.contains(pattern, case=False, na=False)].head(8)
    
    results = []
    for _, row in subset.iterrows():
        year_match = re.search(r'\((\d{4})\)', str(row['title']))
        year = year_match.group(1) if year_match else ""
        raw_p = fetch_wiki_poster(row['clean_title'], year)
        results.append({
            "movieId": int(row['movieId']),
            "title": row['title'],
            "clean_title": row['clean_title'],
            "year": year,
            "genres": row['genres'],
            "poster_url": make_poster_endpoint(raw_p, row['clean_title'])
        })
        
    payload = {
        "mood": mood,
        "genres": target_genres,
        "movies": results
    }
    set_cached_query(cache_key, payload)
    return jsonify(payload)

if __name__ == "__main__":
    print("🚀 Starting CinePulse Advanced Hybrid Recommender on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
