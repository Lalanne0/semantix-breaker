document.addEventListener('DOMContentLoaded', () => {
    // View Containers
    const menuLayout = document.getElementById('menu-layout');
    const playLayout = document.getElementById('play-layout');
    const crackLayout = document.getElementById('crack-layout');
    
    // Menu Buttons
    const modePlayBtn = document.getElementById('mode-play-btn');
    const modeCrackBtn = document.getElementById('mode-crack-btn');
    const playBackBtn = document.getElementById('play-back-btn');
    const crackBackBtn = document.getElementById('crack-back-btn');

    // Play Mode Elements
    const form = document.getElementById('guess-form');
    const input = document.getElementById('guess-input');
    const submitBtn = document.getElementById('guess-button');
    const hintBtn = document.getElementById('hint-button');
    const messageArea = document.getElementById('message-area');
    const guessesList = document.getElementById('guesses-list');
    const guessCountSpan = document.getElementById('guess-count');
    const victoryScreen = document.getElementById('victory-screen');
    const winningWordSpan = document.getElementById('winning-word');
    const newGameBtn = document.getElementById('new-game-button');
    
    // Crack Mode Elements
    const crackForm = document.getElementById('crack-form');
    const crackWordInput = document.getElementById('crack-word');
    const crackTempInput = document.getElementById('crack-temp');
    const crackAddBtn = document.getElementById('crack-add-btn');
    const crackMessageArea = document.getElementById('crack-message-area');
    const crackSuggestionsContainer = document.getElementById('crack-suggestions');
    const crackList = document.getElementById('crack-list');
    const crackCountSpan = document.getElementById('crack-count');
    const crackResetBtn = document.getElementById('crack-reset-btn');

    const loadingOverlay = document.getElementById('loading-overlay');

    // State
    let currentMode = 'menu'; // menu | play | crack
    let currentLang = 'en'; // default language
    let guesses = [];
    let isGameWon = false;
    let crackHistory = [];

    // Initialize Game
    async function startGame() {
        showLoading(true);
        try {
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lang: currentLang })
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                resetUI();
            } else {
                showError('Failed to start game. Please refresh.');
            }
        } catch (error) {
            console.error('Error starting game:', error);
            showError('Server error. Please check your connection.');
        } finally {
            showLoading(false);
            input.focus();
        }
    }

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (isGameWon) return;

        const guess = input.value.trim().toLowerCase();
        if (!guess) return;

        // Check if already guessed
        if (guesses.some(g => g.word === guess)) {
            showError(`You already guessed '${guess}'!`);
            input.value = '';
            return;
        }

        setLoadingState(true);
        hideMessage();

        try {
            const response = await fetch('/api/guess', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ word: guess })
            });
            
            const data = await response.json();

            if (data.status === 'success') {
                addGuess(data.word, data.temperature, data.isMatch);
                if (data.isMatch) {
                    handleVictory(data.word);
                }
            } else {
                showError(data.message);
            }
        } catch (error) {
            console.error('Error guessing word:', error);
            showError('Network error while processing guess.');
        } finally {
            setLoadingState(false);
            input.value = '';
            input.focus();
        }
    });

    // Handle Hint request
    hintBtn.addEventListener('click', async () => {
        if (isGameWon) return;

        setLoadingState(true);
        hideMessage();

        try {
            // 1. Ask the server for a hint word
            const hintResponse = await fetch('/api/hint');
            const hintData = await hintResponse.json();

            if (hintData.status !== 'success' || !hintData.hint) {
                showError(hintData.message || 'No hints available.');
                return;
            }

            const hintWord = hintData.hint;

            // 2. Immediately submit the hint as a guess so we get its score
            const guessResponse = await fetch('/api/guess', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ word: hintWord })
            });
            const guessData = await guessResponse.json();

            if (guessData.status === 'success') {
                addGuess(guessData.word, guessData.temperature, guessData.isMatch, true);
                if (guessData.isMatch) {
                    handleVictory(guessData.word);
                }
            } else {
                showError('Failed to apply the hint.');
            }
        } catch (error) {
            console.error('Hint error:', error);
            showError('Network error while fetching hint.');
        } finally {
            setLoadingState(false);
            input.focus();
        }
    });

    // Add guess to array and re-render
    function addGuess(word, temperature, isMatch, isHint = false) {
        guesses.push({ word, temperature, timestamp: Date.now(), isHint });
        
        // Sort guesses by temperature (highest first)
        guesses.sort((a, b) => b.temperature - a.temperature);
        
        renderGuesses();
        guessCountSpan.textContent = guesses.length;
    }

    // Render the guesses list
    function renderGuesses() {
        guessesList.innerHTML = '';
        
        // Find the min/max temperature for scaling the visual logic
        // The game gives roughly -100 to +100.
        // Let's normalize 0% width to -100, and 100% width to +100
        
        guesses.forEach(item => {
            const card = document.createElement('div');
            card.className = `guess-card ${item.isHint ? 'is-hint' : ''}`;
            
            // Map temperature from [-100, 100] to a percentage [0, 100] for UI width
            // Since some words might be lower than -100 (rarely) or exact match is 100
            let percentage = ((item.temperature + 100) / 200) * 100;
            percentage = Math.max(0, Math.min(100, percentage)); // Clamp between 0-100%

            // Determine color based on temperature
            let colorVar = 'var(--temp-ice)';
            if (item.temperature > 80) colorVar = 'var(--temp-hot)';
            else if (item.temperature > 40) colorVar = 'var(--temp-warm)';
            else if (item.temperature > -20) colorVar = '#a371f7'; // Neutral purple/blue
            
            const hintBadge = item.isHint ? `<span style="font-size: 0.8em; color: var(--accent-color); border: 1px solid var(--accent-color); padding: 2px 6px; border-radius: 10px; margin-left: 8px; font-weight: 300;">💡 Hint</span>` : '';
            
            card.innerHTML = `
                <div class="guess-info">
                    <span class="guess-word">${item.word} ${hintBadge}</span>
                    <span class="guess-temp" style="color: ${colorVar}">${item.temperature.toFixed(2)} °C</span>
                </div>
                <div class="temp-bar-bg">
                    <div class="temp-bar-fill" style="width: 0%; background: ${colorVar}"></div>
                </div>
            `;
            
            guessesList.appendChild(card);

            // Animate after brief delay so transition triggers
            setTimeout(() => {
                const fillBar = card.querySelector('.temp-bar-fill');
                if (fillBar) fillBar.style.width = `${percentage}%`;
            }, 50);
        });
    }

    function handleVictory(word) {
        isGameWon = true;
        input.disabled = true;
        submitBtn.disabled = true;
        winningWordSpan.textContent = word;
        victoryScreen.classList.remove('hidden');
    }

    function resetUI() {
        guesses = [];
        isGameWon = false;
        input.disabled = false;
        submitBtn.disabled = false;
        input.value = '';
        guessCountSpan.textContent = '0';
        guessesList.innerHTML = '';
        hideMessage();
        victoryScreen.classList.add('hidden');
    }

    // Event listeners
    newGameBtn.addEventListener('click', startGame);

    // Helpers
    function showError(msg) {
        messageArea.textContent = msg;
        messageArea.className = 'message error';
        messageArea.classList.remove('hidden');
    }

    function hideMessage() {
        messageArea.classList.add('hidden');
    }

    function setLoadingState(isLoading) {
        input.disabled = isLoading;
        submitBtn.disabled = isLoading;
        hintBtn.disabled = isLoading;
        if (isLoading) {
            submitBtn.textContent = '...';
        } else {
            submitBtn.textContent = 'Guess';
        }
    }

    function showLoading(isVisible) {
        if (isVisible) {
            loadingOverlay.style.display = 'flex';
            setTimeout(() => { loadingOverlay.style.opacity = '1'; }, 10);
        } else {
            loadingOverlay.style.opacity = '0';
            setTimeout(() => { loadingOverlay.style.display = 'none'; }, 500);
        }
    }

    // --- VIEW MANAGEMENT ---
    function switchMode(mode) {
        currentMode = mode;
        menuLayout.classList.add('hidden');
        playLayout.classList.add('hidden');
        crackLayout.classList.add('hidden');

        if (mode === 'menu') {
            menuLayout.classList.remove('hidden');
        } else if (mode === 'play') {
            playLayout.classList.remove('hidden');
            startGame();
        } else if (mode === 'crack') {
            crackLayout.classList.remove('hidden');
            initCrackMode();
        }
    }

    const languageSelect = document.getElementById('language-select');
    languageSelect.addEventListener('change', (e) => {
        currentLang = e.target.value;
    });

    modePlayBtn.addEventListener('click', () => switchMode('play'));
    modeCrackBtn.addEventListener('click', () => switchMode('crack'));
    playBackBtn.addEventListener('click', () => switchMode('menu'));
    crackBackBtn.addEventListener('click', () => switchMode('menu'));

    // --- CRACK MODE LOGIC ---
    async function initCrackMode() {
        crackHistory = [];
        updateCrackUI();
        await fetchCrackSuggestions();
        setTimeout(() => crackWordInput.focus(), 100);
    }

    crackResetBtn.addEventListener('click', () => {
        initCrackMode();
    });

    crackForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const word = crackWordInput.value.trim().toLowerCase();
        const temp = parseFloat(crackTempInput.value);
        
        if (!word || isNaN(temp)) return;
        
        if (crackHistory.some(h => h.word === word)) {
            showCrackError(`You already added '${word}'!`);
            return;
        }

        hideCrackMessage();
        crackWordInput.disabled = true;
        crackTempInput.disabled = true;
        crackAddBtn.disabled = true;
        showLoading(true);

        try {
            // Add to history
            crackHistory.push({ word, temperature: temp });
            // Sort history by reverse temperature for UI display
            crackHistory.sort((a, b) => b.temperature - a.temperature);
            
            updateCrackUI();
            await fetchCrackSuggestions();
        } finally {
            showLoading(false);
            crackWordInput.disabled = false;
            crackTempInput.disabled = false;
            crackAddBtn.disabled = false;
            crackWordInput.value = '';
            crackTempInput.value = '';
            crackWordInput.focus();
        }
    });

    async function fetchCrackSuggestions() {
        try {
            const response = await fetch('/api/crack/suggest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ history: crackHistory, lang: currentLang })
            });
            const data = await response.json();
            
            crackSuggestionsContainer.innerHTML = '';
            
            if (data.status === 'success' && data.suggestions) {
                data.suggestions.forEach(suggestion => {
                    const el = document.createElement('div');
                    el.className = 'suggestion-item';
                    el.textContent = suggestion;
                    
                    // Allow clicking a suggestion to auto-fill input
                    el.addEventListener('click', () => {
                        crackWordInput.value = suggestion;
                        crackTempInput.focus();
                    });
                    
                    crackSuggestionsContainer.appendChild(el);
                });
            }
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            showCrackError('Failed to fetch suggestions.');
        }
    }

    function updateCrackUI() {
        crackCountSpan.textContent = crackHistory.length;
        crackList.innerHTML = '';
        
        crackHistory.forEach(item => {
            const card = document.createElement('div');
            card.className = 'guess-card';
            
            let percentage = ((item.temperature + 100) / 200) * 100;
            percentage = Math.max(0, Math.min(100, percentage));
            
            let colorVar = 'var(--temp-ice)';
            if (item.temperature > 80) colorVar = 'var(--temp-hot)';
            else if (item.temperature > 40) colorVar = 'var(--temp-warm)';
            else if (item.temperature > -20) colorVar = '#a371f7';
            
            card.innerHTML = `
                <div class="guess-info">
                    <span class="guess-word" style="color: var(--text-primary)">${item.word}</span>
                    <span class="guess-temp" style="color: ${colorVar}">${item.temperature.toFixed(2)} °C</span>
                </div>
                <div class="temp-bar-bg">
                    <div class="temp-bar-fill" style="width: ${percentage}%; background: ${colorVar}"></div>
                </div>
            `;
            crackList.appendChild(card);
        });
    }

    function showCrackError(msg) {
        crackMessageArea.textContent = msg;
        crackMessageArea.className = 'message error';
        crackMessageArea.classList.remove('hidden');
    }

    function hideCrackMessage() {
        crackMessageArea.classList.add('hidden');
    }

    // Rather than start game automatically, display the menu layout.
    // The HTML sets up the correct visibility out of the box.
    showLoading(false);
});
