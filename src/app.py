import os
from flask import Flask, render_template, request, jsonify, session
from model_loader import game_instance

app = Flask(__name__)
# In production, use a secure secret key from environment variables
app.secret_key = os.environ.get('SECRET_KEY', 'semantix-breaker-dev-key')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_game():
    target_word = game_instance.get_random_word()
    session['target_word'] = target_word
    # Clear the previous guess history if it was stored
    session['guess_history'] = []
    
    # We do not return the target word. We only confirm success.
    # In a real secure app, we wouldn't show the word in plain text in logs.
    print(f"DEBUG: New target word initialized: {target_word}")
    
    return jsonify({
        "status": "success",
        "message": "Game started. A new hidden word has been selected."
    })

@app.route('/api/guess', methods=['POST'])
def guess_word():
    # Make sure we have a session target word
    if 'target_word' not in session:
        return jsonify({"status": "error", "message": "No active game. Please start a new game."}), 400

    target = session['target_word']
    
    data = request.get_json()
    if not data or 'word' not in data:
        return jsonify({"status": "error", "message": "Missing 'word' in JSON body."}), 400
        
    guessed_word = data['word'].strip().lower()
    
    if not guessed_word:
        return jsonify({"status": "error", "message": "Word cannot be empty."}), 400

    # Ensure it's in the vocabulary
    if not game_instance.is_valid_word(guessed_word):
        return jsonify({"status": "error", "message": f"'{guessed_word}' not found in dictionary."}), 400

    # Calculate similarity
    similarity = game_instance.get_similarity(guessed_word, target)
    
    if similarity is None:
        return jsonify({"status": "error", "message": f"Could not calculate similarity for '{guessed_word}'."}), 400

    # Store the guess in session so we don't give it as a hint later
    if 'guess_history' not in session:
        session['guess_history'] = []
    if guessed_word not in session['guess_history']:
        session['guess_history'].append(guessed_word)
        session.modified = True

    # Check for a match
    is_match = (guessed_word == target)
    
    return jsonify({
        "status": "success",
        "word": guessed_word,
        "temperature": similarity,
        "isMatch": is_match
    })

@app.route('/api/hint', methods=['GET'])
def get_hint():
    if 'target_word' not in session:
        return jsonify({"status": "error", "message": "No active game."}), 400
        
    target = session['target_word']
    previous_guesses = session.get('guess_history', [])
    
    hint_word = game_instance.get_hint(target, previous_guesses)
    
    if not hint_word:
        return jsonify({"status": "error", "message": "Could not generate a hint."}), 500
        
    return jsonify({
        "status": "success",
        "hint": hint_word
    })

if __name__ == '__main__':
    # Run the app locally over port 5005
    app.run(host='0.0.0.0', port=5005, debug=True)
