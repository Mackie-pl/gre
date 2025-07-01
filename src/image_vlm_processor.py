import os
import json
from openai import OpenAI
from typing import List, Dict, Any, Optional
from db_connector import DBConnector

openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8000/v1"

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=openai_api_key,
    base_url=openai_api_base,
)

# models = client.models.list()
model = "google/gemma-3-4b-it"

# we need to send smth like this using openAi package:
# {
#     "model": "HuggingFaceTB/SmolVLM2-2.2B-Instruct",
# 	 	"messages":[{
#       "role": "user",
# 			"content": [
# 				{
# 					"type": "text",
# 					"text": "What's in this image?"
# 				},
# 				{
# 					"type": "image_url",
# 					"image_url": {
# 						"url": "https://play-lh.googleusercontent.com/TuldCmJnsld3yG9AG_vvVsWtJQhd0KGOekfZgZpjqGiT-CVQ3J5uuUyMEdF7e6X86W29"
# 					}
# 				}
# 			]
# 		}],
#     "max_tokens": 777,
#     "temperature": 0
#   }

prompt_text = """Describe visible game elements all provided screenshots. The description can include UI components (including text, numbers, and buttons), characters (type, appearance, equipment), environment (terrain, structures, background elements), game objects (blocks, items, creatures), etc.

Be sure to include layout description, art style, overall vibe etc.

Use concise technical language. Avoid lists, bullet points, or other formatting. No introductions or subjective descriptions.

Keep it around 500 characters."""


class ScreenshotVLMProcessor:
    def __init__(
        self,
        model_name: str = "google/gemma-3-4b-it",
        output_dir: str = "data/screenshots",
    ):
        self.model_name = model_name
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.client = OpenAI(
            api_key="EMPTY",
            base_url="http://localhost:8000/v1",
        )

    def process_game_screenshots(
        self, games: List[Dict[str, Any]], progress_bar: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        print(f"Processing screenshots for {len(games)} games...")

        for i, game in enumerate(games):
            game_id = game["app_id"]
            screenshots_JSON_str = game["photos"]
            screenshots: List[str] = json.loads(screenshots_JSON_str)

            if not screenshots:
                DBConnector().add_data_to_game(game_id, {"screenshot_captions": []})
                continue

            # Process up to 3 screenshots per game (to save time)
            screenshots = screenshots[:3]

            # for j, screenshot_url in enumerate(screenshots):

            msg_content = [
                {
                    "type": "text",
                    "text": prompt_text,
                },
            ]

            for j, screenshot_url in enumerate(screenshots):
                msg_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": screenshot_url},
                    }
                )

            chat_completion_from_url = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": msg_content,
                    }
                ],
                model=self.model_name,
                max_tokens=646,
                temperature=0,
            )

            result = chat_completion_from_url.choices[0].message.content

            DBConnector().add_data_to_game(game_id, {"screenshot_captions": result})
            progress_bar.progress(
                (i + 1) / len(games), text="Processing screenshots..."
            )

        return games
