import streamlit as st
from store_apps_fetcher import StoreAppsFetcher
import shelve
from db_connector import DBConnector
from image_vlm_processor import ScreenshotVLMProcessor
from vector_store import GameVectorStore
from typing import List, Dict, Any

# Set page configuration
st.set_page_config(page_title="Game Fetcher", page_icon="🎮", layout="centered")
st.title("🎮 Game Fetcher")
tab1, tab2, tab3 = st.tabs(
    [
        "Games DB",
        "Vector Store",
        "Fetch",
    ]
)

with tab1:
    st.header("Games DB")
    db = DBConnector()
    st.write("Number of games: " + str(db.get_count()))
    st.write(
        "Games with screenshots captions: "
        + str(db.get_count_with_screenshot_captions())
    )

    def fetch_captions(games: List[Dict[str, Any]]):
        progress_text = "Fetching screenshots captions"
        fetch_captions_bar = st.progress(0, text=progress_text)
        processor = ScreenshotVLMProcessor()
        processor.process_game_screenshots(games, fetch_captions_bar)
        st.rerun()

    if st.button("Fetch screenshots captions"):
        fetch_captions(DBConnector().load_games())

    if st.button("Fetch missing screenshots captions"):
        fetch_captions(DBConnector().load_games_without_screenshot_captions())
with tab2:
    st.write("Number of games in vector store: " + str(GameVectorStore().count_games()))
    if st.button("Add all games to vector store"):
        GameVectorStore().add_games_to_collection(DBConnector().load_games())
        st.rerun()
with tab3:
    with shelve.open("mydata") as db:
        if "credits" not in db:
            db["credits"] = 100

        st.markdown(
            """
            Fetch games from the Google Play Store. Remaining credits: %s
            """
            % db["credits"]
        )

    url_path = st.multiselect(
        "Fetch from",
        StoreAppsFetcher.url_paths,
        default=[StoreAppsFetcher.url_paths[0]],
        format_func=lambda x: x["label"],
    )

    use_categories = st.checkbox("Use categories", value=True)
    if use_categories:
        categories = st.multiselect(
            "Categories",
            StoreAppsFetcher.game_categories,
            default=[StoreAppsFetcher.game_categories[0]],
            format_func=lambda x: x.replace("GAME_", "").replace("_", " ").title(),
        )

    # we'll fetch 2 x the number of categories (or 1 if no categories are selected) * the number of url paths
    num_credits = 2 * (len(categories) if use_categories else 1) * len(url_path)

    if st.button("Fetch (will use " + str(num_credits) + " credits)"):
        fetcher = StoreAppsFetcher()
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
