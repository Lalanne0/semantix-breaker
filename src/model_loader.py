import os
import random
import numpy as np
import gensim.downloader as api
import spacy
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
                print("French Model loaded successfully.")
                self._build_vocab()
            else:
                print("WARNING: French model not found. Falling back to English.")
                self.lang = 'en'
        
        if self.lang == 'en':
            print("Loading English Word2Vec model (word2vec-google-news-300)... This might take a moment on first run.")
            self.model = api.load("word2vec-google-news-300")
            print("English Model loaded successfully.")
            print("English Model loaded successfully.")
            self._build_vocab()

    def _build_vocab(self):
        try:
            if self.lang == 'fr':
                nlp = spacy.load("fr_core_news_sm", disable=["ner", "parser"])
            else:
                nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
        except OSError:
            print(f"SpaCy model for {self.lang} not found.")
            nlp = None

        raw_vocab = [word for word in self.model.index_to_key if word.isalpha() and word.islower()]
        
        if not nlp:
            self.vocab = raw_vocab
            self.target_pool = self.vocab[50:5000]
            return

        print(f"Filtering vocabulary pool for {self.lang} using SpaCy (this takes a few seconds)...")
        self.vocab = []
        
        # Process the top 30,000 words. We want a rich vocab pool for hints too.
        candidates = raw_vocab[50:30000]
        
        for doc in nlp.pipe(candidates, batch_size=1000):
            if len(doc) != 1:
                continue
            token = doc[0]
            pos = token.pos_
            
            is_valid = False
            
            if pos == "VERB":
                # Infinitive verbs
                if "Inf" in token.morph.get("VerbForm", []):
                    is_valid = True
            elif pos == "NOUN":
                # Singular nouns
                if "Plur" not in token.morph.get("Number", []):
                    is_valid = True
            elif pos in ["ADJ", "ADV"]:
                # Adjectives and Adverbs (ensure not plural for French adjectives, though English adj don't have plurals)
                if "Plur" not in token.morph.get("Number", []):
                    is_valid = True
                    
            if is_valid and token.text not in self.vocab:
                self.vocab.append(token.text)
                
            # Stop if we have accumulated enough valid words
            if len(self.vocab) >= 15000:
                break
                
        self.target_pool = self.vocab[:5000]
        print(f"Filtered. Vocabulary size: {len(self.vocab)}, Target pool size: {len(self.target_pool)}")

    def get_random_word(self):
        return random.choice(self.target_pool)

    def is_valid_word(self, word):
        # We now check against the filtered vocab to enforce word rules on user input
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
        try:
            # Get the top 100 most similar words
            similar_words = self.model.most_similar(target_word, topn=100)
            
            # Filter out words that the user has already guessed
            # And also ensure the hint is in our valid vocabulary pool
            valid_hints = []
            
            for word, similarity in similar_words:
                cleaned_word = word.lower()
                # Skip if already guessed, or if it isn't in our clean filtered vocab
                if cleaned_word in previous_guesses or cleaned_word not in self.vocab:
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
        
        errors = []
        # We search through the target pool (the top 5000 common words)
        for candidate in self.target_pool:
            if candidate in guessed_words:
                continue
                
            mae = 0
            for item in valid_history:
                sim = self.get_similarity(item['word'], candidate)
                if sim is None:
                    # Fallback to mean error if we somehow cannot compute
                    mae += 100 
                else:
                    mae += abs(sim - item['temperature'])
                
            errors.append((candidate, mae))
            
        # Sort candidates by minimum error compared to the inputs
        errors.sort(key=lambda x: x[1])
        
        # Return top 10 best guesses
        return [w[0] for w in errors[:10]]

# Factory for instantiated games
game_instances = {
    'en': WordEmbeddingGame('en'),
    # Fr instance is created identically but loads fr_model.kv, if it exists
    'fr': WordEmbeddingGame('fr')
}
