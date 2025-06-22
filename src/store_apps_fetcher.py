"""
Data fetcher module for the Game Recommendation Engine.
Handles fetching game data from Google Play Store API.
"""

import json
import os
import requests
from typing import List, Dict, Any, Optional
import time
import sqlite3


class StoreAppsFetcher:
    url_paths = [
        {"value": "/top-grossing-apps", "label": "Top Grossing Apps"},
        {"value": "/top-free-apps", "label": "Top Free Apps"},
    ]

    game_categories = [
        "GAME_ARCADE",  # Arcade
        "GAME_PUZZLE",  # Puzzle
        "GAME_CARD",  # Cards
        "GAME_CASUAL",  # Casual
        "GAME_ACTION",  # Action
        "GAME_ADVENTURE",  # Adventure
        "GAME_ROLE_PLAYING",  # Role Playing
        "GAME_SIMULATION",  # Simulation
        "GAME_STRATEGY",  # Strategy
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Google Play Store fetcher.

        Args:
            api_key: Optional API key for the Google Play Store API.
        """
        self.api_key = api_key or os.getenv("X_RAPIDAPI_KEY")
        self.base_url = "https://store-apps.p.rapidapi.com"
        self.game_main_category = "GAME"

    def fetch_games(
        self,
        category: str | list[str] = "GAME",
        url_path: str | list[str] = url_paths[0],
    ) -> List[Dict[str, Any]]:
        """
        Fetch games from the Google Play Store.

        Args:
            category: Category of apps to fetch.
            url_path: URL path to fetch from.

        Returns:
            List of game data dictionaries.
        """
        print("Fetching games from Google Play Store...")

        games = []
        page_size = 200

        cat_list = [category] if isinstance(category, str) else category
        url_paths = [url_path] if isinstance(url_path, str) else url_path

        # log to console
        print(
            f"Fetching games from Google Play Store with category: {cat_list} and url path: {url_paths}"
        )

        for cat in cat_list:
            for url_path in url_paths:
                try:
                    response = self._make_api_request(
                        page_size=page_size, category=cat, url_path=url_path
                    )

                    if response.get("status") != "OK" or not response.get("data"):
                        print(
                            f"No more games found or API error. Total games fetched: {len(games)}"
                        )
                        break

                    batch = response["data"]
                    games.extend(batch)
                    print(f"Fetched batch of {len(batch)} games. Total: {len(games)}")

                    # Break if we got fewer items than requested (last page)
                    if len(batch) < page_size:
                        break

                    time.sleep(1)  # Avoid rate limiting

                except Exception as e:
                    print(f"Error fetching games: {e}")
                    break

        return games

    def _make_api_request(
        self,
        page_size: int = 200,
        category: str = "GAME",
        url_path: str = "/top-grossing-apps",
    ) -> Dict[str, Any]:
        """
        Make an API request to the Google Play Store API.

        Args:
            page_size: Number of items per page.
            category: App category.

        Returns:
            API response as dictionary.
        """
        params = {
            "category": category,
            "url_path": url_path,
            "limit": page_size,
        }

        headers = {}
        if self.api_key:
            headers["x-rapidapi-key"] = self.api_key
            headers["x-rapidapi-host"] = "store-apps.p.rapidapi.com"

        url = self.base_url + url_path

        response = requests.get(url, params=params, headers=headers)

        if response.status_code != 200:
            print(f"API Error: {response.status_code} - {response.text}")
            return {"status": "ERROR", "data": []}

        return response.json()

    def save_games_to_file(self, games: List[Dict[str, Any]], filepath: str) -> None:
        """
        Save games data to a JSON file.

        Args:
            games: List of game data dictionaries.
            filepath: Path to save the JSON file.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"games": games}, f, indent=2)

        print(f"Saved {len(games)} games to {filepath}")

    def save_games_to_db(self, games: List[Dict[str, Any]]) -> None:
        """
        Save games data to a SQLite database.

        Args:
            games: List of game data dictionaries.
        """
        filepath = "data/games.db"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        con = sqlite3.connect(filepath)
        cursor = con.cursor()

        # Create the main apps table with all values including photos as JSON
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS apps (
            app_id TEXT PRIMARY KEY,
            app_name TEXT,
            app_category TEXT,
            app_category_id TEXT,
            app_developer TEXT,
            num_downloads TEXT,
            app_description TEXT,
            app_page_link TEXT,
            price REAL,
            price_currency TEXT,
            is_paid BOOLEAN,
            rating REAL,
            app_icon TEXT,
            trailer TEXT,
            num_downloads_exact INTEGER,
            app_content_rating TEXT,
            chart_label TEXT,
            chart_rank INTEGER,
            app_updated_at_timestamp INTEGER,
            app_updated_at_datetime_utc TEXT,
            num_ratings INTEGER,
            num_reviews INTEGER,
            app_first_released_at_datetime_utc TEXT,
            app_first_released_at_timestamp INTEGER,
            current_version TEXT,
            current_version_released_at_timestamp INTEGER,
            current_version_released_at_datetime_utc TEXT,
            current_version_whatsnew TEXT,
            privacy_policy_link TEXT,
            contains_ads BOOLEAN,
            app_developer_website TEXT,
            app_developer_email TEXT,
            min_android_version TEXT,
            min_android_api_level INTEGER,
            max_android_version TEXT,
            max_android_api_level INTEGER,
            photos TEXT
        )""")

        # Insert data into the main apps table
        for game in games:
            # Convert photos dict to JSON string first
            photos = game.get("photos", {})
            photos_json = json.dumps(photos) if photos else "{}"

            # Extract all scalar values
            cursor.execute(
                """
            INSERT OR REPLACE INTO apps (
                app_id, app_name, app_category, app_category_id, app_developer,
                num_downloads, app_description, app_page_link, price,
                price_currency, is_paid, rating, app_icon, trailer,
                num_downloads_exact, app_content_rating, chart_label,
                chart_rank, app_updated_at_timestamp, app_updated_at_datetime_utc,
                num_ratings, num_reviews, app_first_released_at_datetime_utc,
                app_first_released_at_timestamp, current_version,
                current_version_released_at_timestamp, current_version_released_at_datetime_utc,
                current_version_whatsnew, privacy_policy_link, contains_ads,
                app_developer_website, app_developer_email, min_android_version,
                min_android_api_level, max_android_version, max_android_api_level,
                photos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    game.get("app_id"),
                    game.get("app_name"),
                    game.get("app_category"),
                    game.get("app_category_id"),
                    game.get("app_developer"),
                    game.get("num_downloads"),
                    game.get("app_description"),
                    game.get("app_page_link"),
                    game.get("price"),
                    game.get("price_currency"),
                    game.get("is_paid"),
                    game.get("rating"),
                    game.get("app_icon"),
                    game.get("trailer"),
                    game.get("num_downloads_exact"),
                    game.get("app_content_rating"),
                    game.get("chart_label"),
                    game.get("chart_rank"),
                    game.get("app_updated_at_timestamp"),
                    game.get("app_updated_at_datetime_utc"),
                    game.get("num_ratings"),
                    game.get("num_reviews"),
                    game.get("app_first_released_at_datetime_utc"),
                    game.get("app_first_released_at_timestamp"),
                    game.get("current_version"),
                    game.get("current_version_released_at_timestamp"),
                    game.get("current_version_released_at_datetime_utc"),
                    game.get("current_version_whatsnew"),
                    game.get("privacy_policy_link"),
                    game.get("contains_ads"),
                    game.get("app_developer_website"),
                    game.get("app_developer_email"),
                    game.get("min_android_version"),
                    game.get("min_android_api_level"),
                    game.get("max_android_version"),
                    game.get("max_android_api_level"),
                    photos_json,
                ),
            )

            app_id = game.get("app_id")

        # Commit and close
        con.commit()
        con.close()

        print(f"Saved {len(games)} apps to database at {filepath}")

    def load_games_from_db(self) -> List[Dict[str, Any]]:
        filepath = "data/games.db"
        con = sqlite3.connect(filepath)
        con.row_factory = sqlite3.Row
        cursor = con.cursor()

        cursor.execute("SELECT * FROM apps")
        games = cursor.fetchall()

        con.close()

        return games


if __name__ == "__main__":
    # Example usage
    fetcher = StoreAppsFetcher()
    games = fetcher.fetch_games(
        limit=200, category=fetcher.game_main_category, url_path=fetcher.url_paths[0]
    )
    # fetcher.save_games_to_file(games, "data/games.json")
    fetcher.save_games_to_db(games)
