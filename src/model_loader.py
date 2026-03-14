import os
import random
import numpy as np
import gensim.downloader as api
from flask import current_app

class WordEmbeddingGame:
    def __init__(self, lang='en'):
        self.lang = lang
        
        if lang == 'fr':
            print("Loading French Embedding model...")
            model_path = os.path.join(os.path.dirname(__file__), "fr_model.kv")
            if os.path.exists(model_path):
                from gensim.models import KeyedVectors
                self.model = KeyedVectors.load(model_path)
                print("French Model loaded successfully.")
                self._build_vocab()
            else:
                print("WARNING: French model not found. Falling back to English.")
                self.lang = 'en'
        
        if self.lang == 'en':
            print("Loading English Word2Vec model (word2vec-google-news-300)... This might take a moment on first run.")
            self.model = api.load("word2vec-google-news-300")
            print("English Model loaded successfully.")
            self._build_vocab()

    def _build_vocab(self):
        raw_vocab = [word for word in self.model.index_to_key if word.isalpha() and word.islower()]
        self.vocab = set(raw_vocab)
        self.target_pool = raw_vocab[50:5000]

    def get_random_word(self):
        return random.choice(self.target_pool)

    def is_valid_word(self, word):
        # We check against the vocab to enforce word rules on user input
        return word in self.vocab

    def get_similarity(self, word1, word2):
        try:
            # Calculate cosine similarity (returns a value between -1.0 and 1.0)
            sim = self.model.similarity(word1, word2)
            
            # The prompt asks for a "temperature" varying between -100 and 100
            # A simple scaling is to multiply by 100
            temperature = float(sim * 100)
            
            # If it's exactly the same word, make sure it returns 100
            if word1 == word2:
                temperature = 100.0
                
            return round(temperature, 2)
        except KeyError:
            return None

    def get_hint(self, target_word, previous_guesses):
        """Return a single hint word that is semantically related to the target.

        The word is chosen from a medium-similarity band so it is helpful
        without being a dead giveaway.  Previously guessed words and words
        outside the filtered vocabulary are excluded.
        """
        try:
            # Restrict the search to the top 15k most-frequent words.
            # This keeps the lookup fast (~ms) instead of scanning the full
            # multi-million-word model which can take 10-30 seconds.
            neighbours = self.model.most_similar(
                target_word, topn=100, restrict_vocab=15000
            )
        except KeyError:
            return None

        # Build a set for O(1) lookups on previously guessed words
        guessed = set(w.lower() for w in previous_guesses)

        # Keep only words that (a) haven't been guessed yet and
        # (b) belong to our curated vocabulary (lowercase, alpha-only).
        candidates = []
        for word, _score in neighbours:
            normalised = word.lower()
            if normalised in guessed or normalised == target_word:
                continue
            if normalised not in self.vocab:
                continue
            candidates.append(normalised)

        if not candidates:
            return None

        # Pick from a medium-similarity band (indices 5–25) so the hint
        # isn't the single most obvious synonym.  Fall back to the full
        # list when there aren't enough candidates.
        lo = min(5, len(candidates) - 1)
        hi = min(25, len(candidates))

        if lo >= hi:
            return random.choice(candidates)

        return random.choice(candidates[lo:hi])

    def get_crack_suggestions(self, history):
        # Initial spread-out words to get bearing if history is empty
        if self.lang == 'fr':
            default_suggestions = ["espace", "animal", "technologie", "émotion", "musique", "nourriture", "couleur", "sports", "science", "politique"]
        else:
            default_suggestions = ["space", "animal", "technology", "emotion", "music", "food", "color", "sports", "science", "politics"]
        
        if not history:
            return default_suggestions
            
        valid_history = []
        for item in history:
            word = item.get('word', '').lower()
            try:
                temp = float(item.get('temperature', 0))
            except (ValueError, TypeError):
                continue
                
            if self.is_valid_word(word):
                valid_history.append({'word': word, 'temperature': temp})
                
        if not valid_history:
            return default_suggestions
        
        guessed_words = set(h['word'] for h in valid_history)
        
        # We search through the target pool (the top 5000 common words)
        # using vectorized operations for speed
        other_words = tuple(self.target_pool)
        errors = np.zeros(len(self.target_pool))
        
        for item in valid_history:
            history_word = item['word']
            target_temp = item['temperature']
            try:
                # gensim distances returns (1 - cosine_similarity)
                # so similarity = 1 - distances
                dists = self.model.distances(history_word, other_words)
                sims = 1.0 - dists
                temps = np.round(sims * 100, 2)
                
                # if the word is exactly the same, enforce 100
                # though usually distance is 0, so sim = 1, temp = 100
                errors += np.abs(temps - target_temp)
            except KeyError:
                errors += 100
                
        # Sort candidates by minimum error compared to the inputs
        sorted_indices = np.argsort(errors)
        
        # Return top 10 best guesses
        top_guesses = []
        for idx in sorted_indices:
            candidate = self.target_pool[idx]
            if candidate not in guessed_words:
                top_guesses.append(candidate)
            if len(top_guesses) >= 10:
                break
                
        return top_guesses

# Factory for instantiated games
game_instances = {
    'en': WordEmbeddingGame('en'),
    # Fr instance is created identically but loads fr_model.kv, if it exists
    'fr': WordEmbeddingGame('fr')
}
