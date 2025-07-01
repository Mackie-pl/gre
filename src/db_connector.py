import sqlite3
from typing import List, Dict, Any
import json


class DBConnector:
    filepath = "data/games.db"

    def __init__(self):
        pass

    def load_games(self) -> List[Dict[str, Any]]:
        con = sqlite3.connect(DBConnector.filepath)
        con.row_factory = sqlite3.Row
        cursor = con.cursor()

        cursor.execute("SELECT * FROM apps")
        games = cursor.fetchall()

        con.close()

        return games

    def load_games_without_screenshot_captions(self) -> List[Dict[str, Any]]:
        con = sqlite3.connect(DBConnector.filepath)
        con.row_factory = sqlite3.Row
        cursor = con.cursor()

        cursor.execute("SELECT * FROM apps WHERE screenshot_captions IS NULL")
        games = cursor.fetchall()

        con.close()

        return games

    def add_games(self, games: List[Dict[str, Any]]):
        con = sqlite3.connect(DBConnector.filepath)
        cursor = con.cursor()

        for game in games:
            cursor.execute(
                "INSERT OR IGNORE INTO apps (app_id, app_name, app_category, app_category_id, app_developer, num_downloads, app_description, app_page_link, price, price_currency, is_paid, rating, app_icon, trailer, num_downloads_exact, app_content_rating, chart_label, chart_rank, app_updated_at_timestamp, app_updated_at_datetime_utc, num_ratings, num_reviews, app_first_released_at_datetime_utc, app_first_released_at_timestamp, current_version, current_version_released_at_timestamp, current_version_released_at_datetime_utc, current_version_whatsnew, privacy_policy_link, contains_ads, app_developer_website, app_developer_email, min_android_version, min_android_api_level, max_android_version, max_android_api_level, photos) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
                    game.get("photos"),
                ),
            )
            con.commit()

        con.close()

    def add_data_to_game(self, app_id: str, data: Dict[str, Any]):
        con = sqlite3.connect(DBConnector.filepath)
        cursor = con.cursor()

        # Check existing columns
        cursor.execute("PRAGMA table_info(apps)")
        columns = [column_info[1] for column_info in cursor.fetchall()]

        # Add any missing columns
        for column_name in data.keys():
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE apps ADD COLUMN {column_name} TEXT")

        # Construct dynamic UPDATE statement
        set_clauses = []
        values = []
        for column_name, value in data.items():
            set_clauses.append(f"{column_name} = ?")
            if isinstance(value, list):
                value = json.dumps(value)
            values.append(value)

        # Add app_id to values for WHERE clause
        values.append(app_id)

        # Execute the dynamic UPDATE
        update_query = f"UPDATE apps SET {', '.join(set_clauses)} WHERE app_id = ?"
        cursor.execute(update_query, values)

        con.commit()
        con.close()

    def get_count(self) -> int:
        con = sqlite3.connect(DBConnector.filepath)
        cursor = con.cursor()
        cursor.execute("SELECT COUNT(*) FROM apps")
        count = cursor.fetchone()[0]
        con.close()
        return count

    def get_count_with_screenshot_captions(self) -> int:
        con = sqlite3.connect(DBConnector.filepath)
        cursor = con.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM apps WHERE screenshot_captions IS NOT NULL"
        )
        count = cursor.fetchone()[0]
        con.close()
        return count
