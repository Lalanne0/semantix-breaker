import gensim.downloader as api

print("Downloading GloVe model (glove-wiki-gigaword-50)...")
api.load("glove-wiki-gigaword-50")
print("Model downloaded successfully!")
