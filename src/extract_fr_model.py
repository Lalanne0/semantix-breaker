import urllib.request
import os
from gensim.models import KeyedVectors
import numpy as np

url = "https://dl.fbaipublicfiles.com/fasttext/vectors-wiki/wiki.fr.vec"
output_path = os.path.join(os.path.dirname(__file__), 'fr_model.kv')
max_words = 60000  # We only need the top 60,000 most frequent French words

print(f"Streaming top {max_words} words from {url}...")

words = []
vectors = []
dim = 300

try:
    with urllib.request.urlopen(url) as response:
        # Read first line (metadata)
        first_line = response.readline().decode('utf-8').strip().split()
        if len(first_line) == 2:
            dim = int(first_line[1])
            print(f"Model metadata: {first_line[0]} words, {dim} dimensions")
        
        count = 0
        for line in response:
            line_str = line.decode('utf-8').rstrip()
            if not line_str:
                continue
                
            parts = line_str.split(' ')
            word = parts[0]
            
            # We only want standard lowercase alphabetical French words to keep it clean for the game
            if word.islower() and word.isalpha():
                try:
                    vec = np.array([float(x) for x in parts[1:]], dtype=np.float32)
                    if len(vec) == dim:
                        words.append(word)
                        vectors.append(vec)
                        count += 1
                except ValueError:
                    pass
                    
            if count >= max_words:
                print(f"Reached {max_words} words. Stopping stream.")
                break

    print(f"Extracted {len(words)} clean words. Creating KeyedVectors...")
    kv = KeyedVectors(vector_size=dim)
    kv.add_vectors(words, vectors)

    print(f"Saving to {output_path}...")
    kv.save(output_path)
    print("Done!")
except Exception as e:
    print(f"Error during streaming: {e}")
    raise
