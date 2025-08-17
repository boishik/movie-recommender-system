🎬 Movie Recommender System

An interactive Movie Recommendation Web App built with Streamlit.
It recommends movies based on content similarity and displays beautiful movie posters using the TMDb API.

🔗 Live Demo: Movie Recommender App

✨ Features

🔍 Search and select a movie from the dropdown

🎯 Get 12 recommended movies instantly

🖼️ Posters displayed in a responsive card grid (4 per row on desktop, 2 per row on mobile)

🌙 Modern dark-themed UI with hover animations

⚡ Fast loading with caching and pre-processed similarity matrix

🛠️ Tech Stack

Python 3.9+

Streamlit – frontend framework

Pandas & NumPy – data handling

Pickle – preprocessed movie data

gdown – for downloading large ML artifacts from Google Drive

TMDb API – posters & metadata


📂 Project Structure
movie-recommender-system/
│── app.py                # Main Streamlit app
│── requirements.txt      # Dependencies
│── .env.sample           # Example API key file
│── .gitignore            # Ignored files (pkl, env, etc.)
│── movie_recommender_system.ipynb   # Notebook (exploration & preprocessing)
│── data/                 # Downloaded artifacts (auto via gdown)
