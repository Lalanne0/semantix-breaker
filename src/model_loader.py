import os
import random
import numpy as np
import gensim.downloader as api
from flask import current_app

class WordEmbeddingGame:
    def __init__(self):
        print("Loading GloVe model (glove-wiki-gigaword-50)... This might take a moment on first run.")
        self.model = api.load("glove-wiki-gigaword-50")
        print("Model loaded successfully.")
        
        # We filter the vocabulary to only include standard alphabetical lowercase words.
        # This prevents the game from picking obscure symbols, numbers, or very rare words as targets.
        self.vocab = [word for word in self.model.index_to_key if word.isalpha() and word.islower()]
        
        # We keep a smaller pool of very common words for the "hidden word" to ensure the game is playable.
        # The top 5000 English words in the GloVe model are generally well-known.
        # We skip the first 50 words as they are often stopwords (the, of, to, and...)
        self.target_pool = self.vocab[50:5000]

    def get_random_word(self):
        return random.choice(self.target_pool)

    def is_valid_word(self, word):
        return word in self.model.key_to_index

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
        try:
            # Get the top 100 most similar words
            similar_words = self.model.most_similar(target_word, topn=100)
            
            # Filter out words that the user has already guessed
            # And also ensure the hint is in our valid vocabulary pool
            valid_hints = []
            
            for word, similarity in similar_words:
                cleaned_word = word.lower()
                # Skip if already guessed, or if it isn't in our clean alphabetical vocab
                if cleaned_word in previous_guesses or not cleaned_word.isalpha() or not cleaned_word.islower():
                    continue
                valid_hints.append(cleaned_word)
                
            if not valid_hints:
                return None
                
            # Pick a word that is moderately close, not the #1 closest word which might be too easy.
            # We'll take something from index 10 to 30 if possible.
            start_idx = min(10, len(valid_hints) - 1)
            end_idx = min(30, len(valid_hints))
            
            # If the list is very short, just pick from what's available
            if start_idx == end_idx:
                start_idx = 0
                
            return random.choice(valid_hints[start_idx:end_idx])
            
        except KeyError:
            return None

# Singleton-like instance to be imported by the Flask app
game_instance = WordEmbeddingGame()
