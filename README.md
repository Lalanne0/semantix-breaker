# Semantix Breaker

Semantix Breaker is an interactive word-guessing game powered by Natural Language Processing and word embeddings. Players try to guess a hidden, randomly chosen word, and each guess receives a "temperature" score based on its semantic similarity to the hidden word. Can you find the target word?

## Features
- Dynamic word selection
- Real-time semantic similarity scoring
- Bilingual support: Available in English and French.

## Setup
Before starting, ensure your Python environment is set up and dependencies are installed from `requirements.txt`. A `venv` directory should be created in the root folder.

## How to Play

### Launching the Game
Start the application simply by running the following command from your terminal:
```bash
make up
```
This command will automatically set up the virtual environment, install dependencies, and start the Flask web server on port `5005`. Once running, open your web browser and navigate to `http://localhost:5005`.

### Stopping the Game
When you are finishing playing, stop the game server by running:
```bash
make down
```
This securely terminates the application running on port `5005`. You can also clean up the environment and python caches by running `make clean`.