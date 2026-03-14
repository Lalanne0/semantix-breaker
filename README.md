# 🧠 Semantix Breaker

A semantic word-guessing game powered by NLP and word embeddings. Guess a hidden word and receive a **temperature** score based on how semantically close your guess is — the hotter, the closer you are!

## ✨ Features

| Feature | Description |
|---|---|
| 🎮 **Play Mode** | Guess the hidden word yourself; each guess gets a similarity temperature |
| 🤖 **Crack Mode** | Feed in word–temperature pairs and let the AI narrow down the answer |
| 💡 **Hints** | Request a hint word from a medium-similarity band |
| 🌐 **Bilingual** | Switch between **English** and **French** on the fly |

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- `make`
- ~1.7 GB free disk space (for the English word2vec model, downloaded on first run)

### Launch

```bash
# Clone the repository
git clone https://github.com/Lalanne0/semantix-breaker.git
cd semantix-breaker

# Start the game (creates venv, installs deps, runs the server)
make up
```

Open **http://localhost:5005** in your browser and play!

### Stop

```bash
make down
```

### Clean up

```bash
# Remove venv and Python caches
make clean
```

## 🐳 Docker

```bash
# Build and run with Docker Compose
docker compose up --build

# Or manually
docker build -t semantix-breaker .
docker run -p 5005:5005 semantix-breaker
```

> **Note:** The Docker build downloads and processes the French word embeddings (~800 MB download). The English model (~1.7 GB) is downloaded on first container start.

## 🇫🇷 French Language Support

The French model is generated from Facebook's FastText wiki vectors. To generate it locally (outside Docker):

```bash
venv/bin/python src/extract_fr_model.py
```

This streams the top 60,000 French words and saves them as `src/fr_model.kv`. The file is gitignored due to its size.

## 🗂 Project Structure

```
semantix-breaker/
├── src/
│   ├── app.py              # Flask application & API routes
│   ├── model_loader.py     # Word embedding game logic
│   ├── extract_fr_model.py # French model generator (one-time setup)
│   ├── static/
│   │   ├── style.css       # UI styling
│   │   └── script.js       # Frontend logic
│   └── templates/
│       └── index.html      # Main page template
├── Dockerfile              # Production container
├── docker-compose.yml      # Compose config
├── Makefile                # Build / run / clean shortcuts
├── requirements.txt        # Python dependencies
└── pyproject.toml          # Project metadata
```

## 📜 License

This project is unlicensed — use it however you like.