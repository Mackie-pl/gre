from openai import OpenAI

# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = "http://localhost:8000/v1"

client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key=openai_api_key,
    base_url=openai_api_base,
)

# models = client.models.list()
model = "google/gemma-3-4b-it"


def run_multi_image() -> None:
    image_url_minecraft = "https://play-lh.googleusercontent.com/TuldCmJnsld3yG9AG_vvVsWtJQhd0KGOekfZgZpjqGiT-CVQ3J5uuUyMEdF7e6X86W29"
    chat_completion_from_url = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Describe visible game elements in this screenshot. The description can include UI components (including text, numbers, and buttons), characters (specify type, appearance, and equipment once), environment (terrain, structures, background elements), game objects (blocks, items, creatures), etc.

Be sure to include layout description, art style, overall vibe etc.

Use concise technical language. Avoid prefacing items with game name. No introductions or subjective descriptions.

Keep it around 500 characters.""",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url_minecraft},
                    },
                ],
            }
        ],
        model=model,
        max_tokens=646,
        temperature=0,
    )

    result = chat_completion_from_url.choices[0].message.content
    print("Chat completion output:", result)


def main() -> None:
    run_multi_image()


if __name__ == "__main__":
    main()
