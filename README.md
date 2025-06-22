# 🎮 Game Vibe Finder

A proof-of-concept game recommendation engine that goes beyond simple genre matching. Find games based on gameplay feelings and visual aesthetics using natural language queries like "something that makes me feel accomplished but not stressed" or "games with the same exploration vibe as Breath of the Wild."

## Features

- **Screenshot Analysis**: Uses image captioning model to extract visual features from game screenshots
- **Semantic Search**: Matches natural language descriptions of vibes and feelings to games
- **Vector Database**: Stores embeddings for efficient similarity search using QDrant
- **LangChain/LangGraph Pipeline**: Orchestrates the recommendation workflow
- **Simple UI**: Streamlit interface for easy interaction

## Project Structure

```
game-rec-poc/
├── data/                   # Data storage
│   └── screenshots/        # Downloaded screenshots
├── models/                 # Model weights and configs
├── src/
│   ├── app.py              # Streamlit application
│   ├── data_fetcher.py     # Google Play Store API client
│   ├── image_processor.py  # Screenshot downloading and analysis
│   ├── vector_store.py     # QDrant vector database manager
│   └── recommendation_engine.py # LangChain/LangGraph pipeline
├── docker-compose.yml      # Docker setup for QDrant
├── requirements.txt        # Python dependencies
└── README.md
```

## Setup & Installation

### Prerequisites

- Python 3.9+
- Docker (for running QDrant)
- Google Play API key (optional, for fetching live data)
- OpenAI API key (for LangChain)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/game-rec-poc.git
cd game-rec-poc
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Start QDrant:

```bash
docker-compose up -d
```

4. Create a `.env` file with your API keys:

```
HUGGING_FACE_HUB_TOKEN=your-hugging-face-hub-token
X_RAPIDAPI_KEY=your-x-rapidapi-key
```

## Running the Application

1. Start the Streamlit app:

```bash
cd game-rec-poc
streamlit run src/app.py
```

2. Open your browser and go to `http://localhost:8501`

3. Click "Initialize Recommendation Engine" in the sidebar

4. Enter a description of the game vibe you're looking for and click "Find Games"

## Sample Queries

Try these example queries:

- "A relaxing game with beautiful landscapes and no combat"
- "Something with cute characters and simple puzzle mechanics"
- "A dark atmospheric game with horror elements but not too scary"
- "Games similar to Candy Crush but with a different theme"

## Limitations

As a proof-of-concept, this project has several limitations:

- The image captioning model is relatively basic and may miss subtle visual elements
- The recommendation quality depends on the size and diversity of the game dataset
- Processing images and generating embeddings can be resource-intensive

## Next Steps

Potential improvements for a production version:

- Switch to a more powerful image understanding model
- Implement user feedback loop to improve recommendations
- Add filtering by device compatibility, price, etc.
- Expand the dataset to include more games and platforms
- Fine-tune embeddings for game-specific language

## License

MIT
