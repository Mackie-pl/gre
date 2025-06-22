"""
Data fetcher module for the Game Recommendation Engine.
Handles fetching game data from Google Play Store API.
"""

import json
import os
import requests
from typing import List, Dict, Any, Optional
import time


class GooglePlayStoreFetcher:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Google Play Store fetcher.

        Args:
            api_key: Optional API key for the Google Play Store API.
        """
        self.api_key = api_key or os.getenv("X_RAPIDAPI_KEY")
        self.base_url = "https://app-stores.p.rapidapi.com/search"

    def fetch_games(
        self, limit: int = 1000, category: str = "GAME"
    ) -> List[Dict[str, Any]]:
        """
        Fetch games from the Google Play Store.

        Args:
            limit: Maximum number of games to fetch.
            category: Category of apps to fetch.

        Returns:
            List of game data dictionaries.
        """
        print(f"Fetching up to {limit} games from Google Play Store...")

        games = []
        page = 1
        page_size = 100

        while len(games) < limit:
            try:
                response = self._make_api_request(
                    page=page, page_size=page_size, category=category
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

                page += 1
                time.sleep(1)  # Avoid rate limiting

            except Exception as e:
                print(f"Error fetching games: {e}")
                break

        return games[:limit]

    def _make_api_request(
        self, page: int = 1, page_size: int = 100, category: str = "GAME"
    ) -> Dict[str, Any]:
        """
        Make an API request to the Google Play Store API.

        Args:
            page: Page number.
            page_size: Number of items per page.
            category: App category.

        Returns:
            API response as dictionary.
        """
        params = {"category": category, "limit": page_size, "page": page}

        headers = {}
        if self.api_key:
            headers["x-rapidapi-key"] = self.api_key
            headers["x-rapidapi-host"] = "app-stores.p.rapidapi.com"

        response = requests.get(self.base_url, params=params, headers=headers)

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

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"games": games}, f, indent=2)

        print(f"Saved {len(games)} games to {filepath}")


if __name__ == "__main__":
    # Example usage
    fetcher = GooglePlayStoreFetcher()
    games = fetcher.fetch_games(limit=100)
    fetcher.save_games_to_file(games, "data/games.json")
