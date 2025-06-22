import streamlit as st
from store_apps_fetcher import GooglePlayStoreFetcher
import shelve

# Set page configuration
st.set_page_config(page_title="Game Fetcher", page_icon="🎮", layout="centered")

with shelve.open("mydata") as db:
    if "credits" not in db:
        db["credits"] = 100
    st.title("🎮 Game Fetcher")
    st.markdown(
        """
        Fetch games from the Google Play Store. Remaining credits: %s
        """
        % db["credits"]
    )

url_path = st.multiselect(
    "Fetch from",
    GooglePlayStoreFetcher.url_paths,
    default=[GooglePlayStoreFetcher.url_paths[0]],
    format_func=lambda x: x["label"],
)

use_categories = st.checkbox("Use categories", value=True)
if use_categories:
    categories = st.multiselect(
        "Categories",
        GooglePlayStoreFetcher.game_categories,
        default=[GooglePlayStoreFetcher.game_categories[0]],
        format_func=lambda x: x.replace("GAME_", "").replace("_", " ").title(),
    )

# we'll fetch 2 x the number of categories (or 1 if no categories are selected) * the number of url paths
num_credits = 2 * (len(categories) if use_categories else 1) * len(url_path)

if st.button("Fetch (will use " + str(num_credits) + " credits)"):
    fetcher = GooglePlayStoreFetcher()
    games = fetcher.fetch_games(
        category=categories, url_path=list(map(lambda x: x["value"], url_path))
    )
    # fetcher.save_games_to_file(games, "data/games.json")
    fetcher.save_games_to_db(games)
    with shelve.open("mydata") as db:
        db["credits"] -= num_credits
    # st.success("Games fetched successfully!")
    # log how many games were fetched
    st.write("Fetched " + str(len(games)) + " games.")
    st.rerun()
