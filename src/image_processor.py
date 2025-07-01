"""
Image processing module for the Game Recommendation Engine.
Handles downloading and analyzing game screenshots.
"""

import os
import requests
from typing import List, Dict, Any, Optional
from PIL import Image
from io import BytesIO
import torch
from tqdm import tqdm
import time
import json
from db_connector import DBConnector
from streamlit import progress


# We'll use a pretrained model for image captioning
# This is a placeholder - in actual implementation, we would import the appropriate model
class ImageCaptioner:
    def __init__(self, model_name: str = "blip-image-captioning-base"):
        """
        Initialize the image captioner.

        Args:
            model_name: Name of the pretrained model to use.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        try:
            # This is a placeholder - in actual implementation, we'd load the appropriate model
            # For example, using Hugging Face's transformers library
            from transformers import BlipProcessor, BlipForConditionalGeneration

            self.processor = BlipProcessor.from_pretrained(f"Salesforce/{model_name}")
            self.model = BlipForConditionalGeneration.from_pretrained(
                f"Salesforce/{model_name}"
            ).to(self.device)
            print(f"Loaded image captioning model: {model_name}")
        except Exception as e:
            print(f"Error loading image captioning model: {e}")
            print("Using dummy captioner instead")
            self.model = None
            self.processor = None

    def generate_caption(self, image) -> str:
        """
        Generate a caption for an image.

        Args:
            image: PIL Image object.

        Returns:
            Caption string.
        """
        if self.model is None or self.processor is None:
            # Return a dummy caption if model failed to load
            return "A screenshot of a mobile game"

        try:
            inputs = self.processor(image, return_tensors="pt").to(self.device)
            output = self.model.generate(**inputs, max_new_tokens=50)
            caption = self.processor.decode(output[0], skip_special_tokens=True)
            return caption
        except Exception as e:
            print(f"Error generating caption: {e}")
            return "Error generating caption for game screenshot"


class ScreenshotProcessor:
    def __init__(self, output_dir: str = "data/screenshots"):
        """
        Initialize the screenshot processor.

        Args:
            output_dir: Directory to save downloaded screenshots.
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.captioner = ImageCaptioner()

    def process_game_screenshots(
        self, games: List[Dict[str, Any]], progress_bar: Optional[progress] = None
    ) -> List[Dict[str, Any]]:
        """
        Process screenshots for a list of games.

        Args:
            games: List of game data dictionaries.

        Returns:
            List of games with added screenshot captions.
        """
        print(f"Processing screenshots for {len(games)} games...")

        for i, game in enumerate(tqdm(games)):
            game_id = game["app_id"]
            screenshots_JSON_str = game["photos"]
            screenshots = json.loads(screenshots_JSON_str)

            if not screenshots:
                DBConnector().add_data_to_game(game_id, {"screenshot_captions": []})
                continue

            # Process up to 3 screenshots per game (to save time)
            screenshots = screenshots[:3]
            captions = []

            for j, screenshot_url in enumerate(screenshots):
                try:
                    # Download and process the screenshot
                    image = self._download_image(screenshot_url)
                    if image:
                        caption = self.captioner.generate_caption(image)
                        captions.append(caption)

                        # Save the screenshot
                        save_path = os.path.join(self.output_dir, f"{game_id}_{j}.jpg")
                        image.save(save_path)
                except Exception as e:
                    print(f"Error processing screenshot {j} for game {game_id}: {e}")

                time.sleep(0.1)  # Avoid rate limiting

            # game["screenshot_captions"] = captions
            DBConnector().add_data_to_game(game_id, {"screenshot_captions": captions})
            progress_bar.progress(
                (i + 1) / len(games), text="Processing screenshots..."
            )

        return games

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """
        Download an image from a URL.

        Args:
            url: URL to download the image from.

        Returns:
            PIL Image object or None if download failed.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
            return None


if __name__ == "__main__":
    # Example usage
    import json

    # Load sample game data
    with open("data/google_play_games.json", "r", encoding="utf-8") as f:
        game_data = json.load(f)

    processor = ScreenshotProcessor()
    processed_games = processor.process_game_screenshots(game_data["games"][:5])

    # Print the generated captions
    for game in processed_games:
        print(f"{game['app_name']}:")
        for caption in game["screenshot_captions"]:
            print(f"  - {caption}")
