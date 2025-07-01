"""
Vector store module for the Game Recommendation Engine.
Handles embedding generation and storage/retrieval using Qdrant.
"""

from typing import List, Dict, Any, Sequence
import numpy as np
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
)
from sqlite3 import Row


class GameVectorStore:
    embedding_model: SentenceTransformer | None = None
    embedding_dim: int | None = None
    client: QdrantClient
    collection_name: str

    def __init__(
        self,
        collection_name: str = "game_recommendations",
        embedding_model_name: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize the game vector store.

        Args:
            collection_name: Name of the Qdrant collection to use.
            embedding_model_name: Name of the SentenceTransformer model to use.
        """
        # Initialize embedding model
        if GameVectorStore.embedding_model is None:
            print(f"Loading embedding model {embedding_model_name}...")
            GameVectorStore.embedding_model = SentenceTransformer(embedding_model_name)
            GameVectorStore.embedding_dim = (
                GameVectorStore.embedding_model.get_sentence_embedding_dimension()
            )
            print(f"Embedding dimension: {GameVectorStore.embedding_dim}")

        # Initialize Qdrant client
        # For local Docker deployment
        GameVectorStore.client = QdrantClient(host="localhost", port=6333)
        GameVectorStore.collection_name = collection_name

    def is_backend_available(self) -> bool:
        try:
            GameVectorStore.client.get_collections()
            return True
        except Exception:
            return False

    def count_games(self) -> int:
        return (
            GameVectorStore.client.get_collection(
                GameVectorStore.collection_name
            ).points_count
            or 0
        )

    def create_collection(self) -> None:
        """
        Create a new collection in Qdrant if it doesn't exist.
        """
        # Check if collection already exists
        collections = GameVectorStore.client.get_collections().collections
        collection_names = [col.name for col in collections]

        if GameVectorStore.collection_name in collection_names:
            print(f"Collection {GameVectorStore.collection_name} already exists.")
            return

        # Create new collection
        print(f"Creating collection {self.collection_name}...")
        if not GameVectorStore.embedding_dim:
            raise ValueError("Embedding dimension is not set.")
        GameVectorStore.client.create_collection(
            collection_name=GameVectorStore.collection_name,
            vectors_config=VectorParams(
                size=GameVectorStore.embedding_dim, distance=Distance.COSINE
            ),
        )
        print(f"Collection {self.collection_name} created successfully.")

    def generate_game_embedding(self, game: Row) -> np.ndarray:
        """
        Generate an embedding for a game based on its attributes.

        Args:
            game: Game data dictionary.

        Returns:
            Numpy array embedding.
        """
        # Combine all relevant text fields for the game
        text_fields: List[str] = []

        # Basic info
        app_name = game["app_name"]
        if app_name:
            text_fields.append(f"Title: {app_name}")

        app_category = game["app_category"]
        if app_category:
            text_fields.append(f"Category: {app_category}")

        app_description = game["app_description"]
        if app_description:
            text_fields.append(f"Description: {app_description}")

        # Screenshot captions (from our image processing)
        screenshot_captions = game["screenshot_captions"]
        if screenshot_captions:
            captions_text = " ".join(
                [f"Screenshot shows: {caption}" for caption in screenshot_captions]
            )
            text_fields.append(captions_text)

        # Join all text fields
        combined_text = " ".join(text_fields)

        # Generate embedding
        embedding = GameVectorStore.embedding_model.encode(combined_text)
        return embedding

    def add_games_to_collection(self, games: Sequence[Row]) -> None:
        """
        Add a list of games to the Qdrant collection.

        Args:
            games: List of game data dictionaries.
        """
        print(f"Adding {len(games)} games to collection {self.collection_name}...")

        # Generate points from games
        points: List[PointStruct] = []
        for game in games:
            try:
                embedding = self.generate_game_embedding(game)

                # Create payload with relevant game info
                payload = {
                    "app_id": game["app_id"],
                    "app_name": game["app_name"],
                    "app_category": game["app_category"],
                    "app_description": game["app_description"][
                        :1000
                    ],  # Truncate long descriptions
                    "rating": game["rating"],
                    "screenshot_captions": game["screenshot_captions"],
                    "app_icon": game["app_icon"],
                    "app_page_link": game["app_page_link"],
                }

                point = PointStruct(
                    id=game["app_id"],  # Use index as ID
                    vector=embedding.tolist(),
                    payload=payload,
                )

                points.append(point)
            except Exception as e:
                print(f"Error processing game {game['app_name']}: {e}")

        # Add points in batches
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)
            print(f"Added {len(points)} games to collection {self.collection_name}")
        else:
            print("No games to add to collection")

    def search_games(
        self, query: str, limit: int = 5, score_threshold: float = 0
    ) -> List[Dict[str, Any]]:
        """
        Search for games similar to the query.

        Args:
            query: Query text.
            limit: Maximum number of results.
            score_threshold: Minimum similarity score.

        Returns:
            List of game data dictionaries.
        """
        print(f"Searching for games matching: '{query}', query length: {len(query)}")

        # Generate embedding for query
        query_embedding = GameVectorStore.embedding_model.encode(query)

        # Search in Qdrant
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=limit,
            score_threshold=score_threshold,
        )

        print(f"Found {len(search_results)} games matching: '{query}'")

        # Extract and format results
        results: List[Dict[str, Any]] = []
        for hit in search_results:
            result = hit.payload
            if not result:
                continue
            result["similarity_score"] = hit.score
            results.append(result)

        return results


if __name__ == "__main__":
    # Example usage
    import json

    # Load sample game data
    with open("data/google_play_games.json", "r", encoding="utf-8") as f:
        game_data = json.load(f)

    vector_store = GameVectorStore()
    vector_store.create_collection()
    vector_store.add_games_to_collection(game_data["games"][:10])

    # Try a search
    results = vector_store.search_games("colorful puzzle game with cute characters")

    # Print results
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['app_name']} (Score: {result['similarity_score']:.4f})")
        print(f"   {result['app_description'][:100]}...")
