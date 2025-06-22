"""
Streamlit application for the Game Recommendation Engine.
"""

import os
import json
import streamlit as st
from PIL import Image
import requests
from io import BytesIO

from store_apps_fetcher import StoreAppsFetcher
from image_processor import ScreenshotProcessor
from vector_store import GameVectorStore
from recommendation_engine import GameRecommendationEngine

# Set page configuration
st.set_page_config(page_title="Game Vibe Finder", page_icon="🎮", layout="wide")

# Initialize session state
if "engine_initialized" not in st.session_state:
    st.session_state.engine_initialized = False

if "games_loaded" not in st.session_state:
    st.session_state.games_loaded = False

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "recommendation_engine" not in st.session_state:
    st.session_state.recommendation_engine = None


# Function to load image from URL
@st.cache_data
def load_image_from_url(url):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None


# Title and description
st.title("🎮 Game Vibe Finder")
st.markdown(
    """
    Beyond simple genre matching - find games based on gameplay feelings and visual aesthetics.
    Try queries like:
    - "Something that makes me feel accomplished but not stressed"
    - "Games with the same colorful exploration vibe as Breath of the Wild"
    - "Dark and moody games with horror elements but not too scary"
    """
)

# Sidebar for setup and configuration
with st.sidebar:
    st.header("Setup")

    # Data source
    data_source = st.selectbox(
        "Data Source",
        ["Local DB", "Sample Data", "Live API (requires API key)"],
        index=0,
    )

    if data_source == "Live API (requires API key)":
        api_key = st.text_input("API Key", type="password")

    st.header("Controls")

    # Setup button
    if st.button("Initialize Recommendation Engine"):
        with st.spinner("Setting up the recommendation engine..."):
            try:
                # Initialize vector store
                vector_store = GameVectorStore()
                vector_store.create_collection()

                # Load games
                if data_source == "Sample Data":
                    # Load from sample data file
                    sample_data_path = "data/sample_games.json"
                    if os.path.exists(sample_data_path):
                        with open(sample_data_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            games = data.get("games", [])
                    else:
                        # Generate minimal sample data
                        games = [
                            {
                                "app_id": "sample_game_1",
                                "app_name": "Sample Adventure Game",
                                "app_category": "GAME_ADVENTURE",
                                "app_description": "An exciting adventure game with puzzles and exploration.",
                                "screenshot_captions": [
                                    "A character exploring a colorful forest",
                                    "A puzzle screen with various objects to interact with",
                                ],
                                "rating": 4.5,
                                "app_icon": "https://example.com/icon1.png",
                            },
                            {
                                "app_id": "sample_game_2",
                                "app_name": "Sample Puzzle Game",
                                "app_category": "GAME_PUZZLE",
                                "app_description": "A challenging puzzle game with colorful visuals.",
                                "screenshot_captions": [
                                    "A grid of colorful blocks to match",
                                    "A victory screen with stars and rewards",
                                ],
                                "rating": 4.2,
                                "app_icon": "https://example.com/icon2.png",
                            },
                        ]
                elif data_source == "Live API (requires API key)":
                    # Use API to fetch games
                    fetcher = StoreAppsFetcher(
                        api_key=api_key
                        if data_source == "Live API (requires API key)"
                        else None
                    )
                    games = fetcher.fetch_games(limit=100)

                elif data_source == "Local DB":
                    # Load from local DB
                    fetcher = StoreAppsFetcher()
                    games = fetcher.load_games_from_db()

                # Process screenshots - NO, they are already processed
                # processor = ScreenshotProcessor()
                # games = processor.process_game_screenshots(games)

                # Add games to vector store
                vector_store.add_games_to_collection(games)

                # Initialize recommendation engine
                engine = GameRecommendationEngine(vector_store=vector_store)

                # Store in session state
                st.session_state.vector_store = vector_store
                st.session_state.recommendation_engine = engine
                st.session_state.engine_initialized = True
                st.session_state.games_loaded = True

                st.success(
                    f"Successfully loaded {len(games)} games into the recommendation engine!"
                )

            except Exception as e:
                st.error(f"Error initializing recommendation engine: {e}")

# Main content area
query = st.text_input(
    "What kind of game are you looking for?",
    placeholder="Describe the vibe, feeling, or visual style you want...",
)

# Search button
if st.button("Find Games"):
    if not st.session_state.engine_initialized:
        st.warning("Please initialize the recommendation engine first!")
    else:
        with st.spinner("Finding games that match your vibe..."):
            try:
                # Generate recommendations
                result = st.session_state.recommendation_engine.recommend_games(query)

                # Display recommendation text
                st.markdown("## Recommendations")
                st.markdown(result["recommendation_text"])

                # Display game cards
                st.markdown("## Game Details")

                # Create columns for game cards
                cols = st.columns(3)

                for i, game in enumerate(result["recommendations"]):
                    col_idx = i % 3
                    with cols[col_idx]:
                        st.markdown(f"### {game['app_name']}")

                        # Display icon if available
                        icon_url = game.get("app_icon")
                        if icon_url:
                            icon = load_image_from_url(icon_url)
                            if icon:
                                st.image(icon, width=100)

                        st.markdown(
                            f"**Category:** {game.get('app_category', 'Unknown')}"
                        )
                        st.markdown(f"**Rating:** {game.get('rating', 'N/A')}")

                        # Display condensed description
                        description = game.get("app_description", "")
                        if description:
                            st.markdown(f"**Description:** {description[:200]}...")

                        # Show what the AI sees in the screenshots
                        captions = game.get("screenshot_captions", [])
                        if captions:
                            st.markdown("**AI sees in screenshots:**")
                            for caption in captions:
                                st.markdown(f"- *{caption}*")

                        # Add link to app page if available
                        app_link = game.get("app_page_link")
                        if app_link:
                            st.markdown(f"[View in Store]({app_link})")

                        st.markdown("---")

            except Exception as e:
                st.error(f"Error generating recommendations: {e}")

# Footer
st.markdown("---")
st.markdown("Game Vibe Finder - A POC using LangChain, LangGraph, and QDrant")
