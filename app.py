# app.py
import os
import math
import pathlib
import pickle
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
import gdown

# -------------------- App config --------------------
st.set_page_config(page_title="Movie Recommender System", layout="wide")

# -------------------- Secrets / .env ----------------
load_dotenv()  # reads .env locally
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
if not TMDB_API_KEY:
    try:
        TMDB_API_KEY = st.secrets["TMDB_API_KEY"]  # used on Streamlit Cloud
    except Exception:
        TMDB_API_KEY = None

# -------------------- Artifact download -------------
DATA_DIR = pathlib.Path("./data")
DATA_DIR.mkdir(exist_ok=True)


MOVIES_URL = "https://drive.google.com/uc?export=download&id=1_1Bn0dTJxYV0l3UBMoDtW3P2HDmQObhl"
SIM_URL    = "https://drive.google.com/uc?export=download&id=1bwJcdFvjWjd7ItusMwhLatXHhZu6kVaa"

def _is_probably_html(path: pathlib.Path) -> bool:
    try:
        with open(path, "rb") as f:
            head = f.read(1)
        return head == b"<"  # HTML interstitials start with '<'
    except Exception:
        return True

def _download(url: str, dest: pathlib.Path):
    """Download to dest. Uses gdown for Google Drive links. Validates that it's not HTML."""
    if dest.exists() and dest.stat().st_size > 0 and not _is_probably_html(dest):
        return
    dest.parent.mkdir(parents=True, exist_ok=True)

    if "drive.google.com" in url:
        # gdown handles Google Drive's confirmation interstitials for large files
        gdown.download(url, str(dest), quiet=False, fuzzy=True)
    else:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 20):  # 1MB chunks
                    if chunk:
                        f.write(chunk)

    # Validate: fail fast if we saved an HTML page or a tiny file
    if _is_probably_html(dest) or dest.stat().st_size < 1000:
        raise RuntimeError(
            f"Downloaded file at {dest} does not look like a pickle. "
            f"Check the URL or file permissions."
        )

@st.cache_resource(show_spinner=True)
def load_artifacts():
    movies_path = DATA_DIR / "movies_dict.pkl"
    sim_path    = DATA_DIR / "similarity.pkl"
    _download(MOVIES_URL, movies_path)
    _download(SIM_URL, sim_path)
    with open(movies_path, "rb") as f:
        movies_dict = pickle.load(f)
    with open(sim_path, "rb") as f:
        similarity = pickle.load(f)
    return movies_dict, similarity

# Load once (download if missing)
movies_dict, similarity = load_artifacts()
movies = pd.DataFrame(movies_dict)

# -------------------- TMDB poster fetch --------------
def fetch_poster(movie_id: int) -> str:
    if not TMDB_API_KEY:
        st.error("TMDB_API_KEY not set. Add it to .env locally or Streamlit Secrets when deployed.")
        return ""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    data = requests.get(url).json()
    poster_path = data.get("poster_path")
    return f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""

# -------------------- Recommender logic ---------------
def recommend(movie_title: str):
    movie_index = movies[movies["title"] == movie_title].index[0]
    distances = similarity[movie_index]
    # top 12 similar (skip the same movie at index 0)
    top = sorted(list(enumerate(distances)), key=lambda x: x[1], reverse=True)[1:13]

    names, posters = [], []
    for idx, _score in top:
        row = movies.iloc[idx]
        names.append(row.title)
        posters.append(fetch_poster(int(row.movie_id)))
    return names, posters

# -------------------- UI ------------------------------
st.title("🎬 Movie Recommender System")

selected_movie = st.selectbox(
    "🎥 Choose a movie to get recommendations:",
    movies["title"].values
)

if st.button("Recommend"):
    names, posters = recommend(selected_movie)

    # Build cards HTML (no indentation inside the string)
    cards = ''.join(
        f'<div class="card"><img src="{posters[i]}"/><p class="t">{names[i]}</p></div>'
        for i in range(len(names))
    )

    # Responsive grid (auto-fit columns). 4 on wide screens, 3/2 as width shrinks.
    html = f"""
<style>
  body {{ margin:0 }}
  .wrap {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 24px;
    width: 100%;
    max-width: 1280px;
    margin: 12px auto 0;
    padding: 0 8px;
  }}
  .card {{
    background:#1e1e1e; border-radius:15px; padding:12px; text-align:center; color:#fff;
    box-shadow:0 4px 10px rgba(0,0,0,.4);
    transition:transform .25s ease, box-shadow .25s ease;
  }}
  .card:hover {{ transform:scale(1.05); box-shadow:0 8px 20px rgba(255,215,0,.6); }}
  .card img {{ width:100%; height:auto; border-radius:10px; display:block; }}
  .t {{ font:600 14px/1.25 "Poppins", system-ui; margin:8px 0 0; color:#FFD700; }}
</style>
<div class="wrap">{cards}</div>
"""

    # Compute a generous iframe height so rows never get clipped
    n_items = len(names)
    cols_guess = 3                         # safe guess (it may be 4 on wide screens)
    rows = math.ceil(n_items / cols_guess)
    approx_card_h = 420                    # poster + title + padding/shadow
    total_h = rows * approx_card_h + 120   # extra margins

    components.html(html, height=total_h, scrolling=False)
