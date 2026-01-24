// Application principale pour l'interface spectacle d'amour
class SpectacleApp {
    constructor() {
        this.selectedWords = [];
        this.allWords = [];
        this.ws = null;
        this.isGenerating = false;
        
        this.init();
    }
    
    async init() {
        // Initialiser WebSocket
        this.initWebSocket();
        
        // Charger les mots initiaux
        await this.loadRandomWords();
        
        // Attacher les événements
        this.attachEvents();
        
        // Mise à jour du status
        this.updateStatus('❤️ Amour(s) en direct - Connexion active');
        
        console.log('🎭 Interface spectacle initialisée');
    }
    
    initWebSocket() {
        try {
            this.ws = new WebSocket('ws://localhost:8080');
            
            this.ws.onopen = () => {
                console.log('📡 WebSocket connecté');
                this.updateStatus('🟢 Spectacle en direct - Connexion active');
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.ws.onclose = () => {
                console.log('📡 WebSocket déconnecté');
                this.updateStatus('🟡 Spectacle en direct - Reconnexion...');
                // Tentative de reconnexion après 3 secondes
                setTimeout(() => this.initWebSocket(), 3000);
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ Erreur WebSocket:', error);
                this.updateStatus('🔴 Spectacle en direct - Problème de connexion');
            };
        } catch (error) {
            console.error('❌ Erreur initialisation WebSocket:', error);
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'phrase_generated':
                console.log('🎵 Phrase générée reçue via WebSocket');
                break;
            default:
                console.log('📨 Message WebSocket:', data);
        }
    }
    
    async loadRandomWords() {
        try {
            const response = await fetch('/api/random-words/19');
            const data = await response.json();
            
            this.allWords = data.words;
            this.renderWordGrid();
        } catch (error) {
            console.error('❌ Erreur chargement mots:', error);
            this.showError('Impossible de charger les mots');
        }
    }
    
    renderWordGrid() {
        const grid = document.getElementById('word-grid');
        grid.innerHTML = '';
        
        this.allWords.forEach((word, index) => {
            const tile = document.createElement('div');
            tile.className = 'word-tile';
            tile.textContent = word;
            tile.dataset.word = word;
            
            // Marquer le mot "amour" spécialement
            if (word.toLowerCase() === 'amour') {
                tile.classList.add('amour');
            }
            
            // Événements tactiles
            tile.addEventListener('click', (e) => this.selectWord(e.target));
            tile.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.selectWord(e.target);
            });
            
            grid.appendChild(tile);
        });
    }
    
    selectWord(tile) {
        const word = tile.dataset.word;
        
        // Effet vibration sur mobile
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        // Animation P5.js
        if (window.onWordSelected) {
            window.onWordSelected();
        }
        
        if (tile.classList.contains('selected')) {
            // Désélectionner
            tile.classList.remove('selected');
            this.selectedWords = this.selectedWords.filter(w => w !== word);
        } else {
            // Sélectionner
            tile.classList.add('selected');
            if (!this.selectedWords.includes(word)) {
                this.selectedWords.push(word);
            }
        }
        
        this.updateSelectedWordsDisplay();
        this.updateGenerateButton();
    }
    
    updateSelectedWordsDisplay() {
        const selectedList = document.getElementById('selected-list');
        selectedList.innerHTML = '';
        
        if (this.selectedWords.length === 0) {
            selectedList.innerHTML = '<p style=\"opacity: 0.7; font-style: italic;\">Aucun mot sélectionné</p>';
        } else {
            this.selectedWords.forEach(word => {
                const wordElement = document.createElement('span');
                wordElement.className = 'selected-word';
                wordElement.textContent = word;
                selectedList.appendChild(wordElement);
            });
        }
    }
    
    updateGenerateButton() {
        const generateBtn = document.getElementById('generate-btn');
        const count = this.selectedWords.length;
        
        if (count > 0) {
            generateBtn.disabled = false;
            generateBtn.textContent = `🎭 Générer ${count} phrase${count > 1 ? 's' : ''}`;
        } else {
            generateBtn.disabled = true;
            generateBtn.textContent = '🎭 Générer vos phrases';
        }
    }
    
    async generatePhrase() {
        if (this.isGenerating || this.selectedWords.length === 0) return;
        
        this.isGenerating = true;
        this.showLoading();
        
        try {
            const response = await fetch('/api/generate-phrase', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    words: this.selectedWords,
                    count: this.selectedWords.length
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayResult(data);
                
                // Animation P5.js
                if (window.onPhraseGenerated) {
                    window.onPhraseGenerated();
                }
                
                // Vibration de succès
                if (navigator.vibrate) {
                    navigator.vibrate([100, 50, 100]);
                }
            } else {
                throw new Error(data.error || 'Erreur de génération');
            }
        } catch (error) {
            console.error('❌ Erreur génération:', error);
            this.showError('Impossible de générer la phrase. Réessayez.');
        } finally {
            this.hideLoading();
            this.isGenerating = false;
        }
    }
    
    displayResult(data) {
        const resultSection = document.getElementById('result');
        const phraseOutput = document.getElementById('phrase-output');
        const audioPlayer = document.getElementById('audio-player');
        
        // Afficher les phrases générées
        if (data.phrases && data.phrases.length > 0) {
            phraseOutput.innerHTML = this.formatPhrases(data.phrases);
        } else if (data.result && data.result.phrases) {
            phraseOutput.innerHTML = this.formatPhrases(data.result.phrases);
        } else {
            phraseOutput.innerHTML = '<p>Phrases générées avec succès!</p>';
        }
        
        // Utiliser le player p5.js si disponible, sinon fallback HTML5
        if (data.audio_url) {
            this.setupP5AudioPlayer(data.audio_url, data);
            
            // Instructions RÉELLES d'utilisation
            const instructions = document.createElement('div');
            instructions.className = 'audio-instructions';
            instructions.innerHTML = `
                <div class="instruction-item">▶️ PLAY/PAUSE - Touchez le gros bouton central</div>
                <div class="instruction-item">⏮️⏭️ PRÉCÉDENT/SUIVANT - Boutons de navigation</div>
                <div class="instruction-item">⏹️ STOP - Bouton d'arrêt complet</div>
                <div class="instruction-item">📜 LIST - Afficher/cacher la playlist complète</div>
                <div class="instruction-item">🎯 Touchez les tracks dans la liste pour les jouer</div>
                <div class="instruction-item">📱 Interface tactile optimisée mobile</div>
            `;
            document.getElementById('p5-audio-container').appendChild(instructions);
            
            // Player de fallback (caché par défaut)
            audioPlayer.innerHTML = `
                <div class="audio-controls">
                    <h4>🎧 Écouter votre création :</h4>
                    <audio controls preload="auto" style="width: 100%; margin: 10px 0;">
                        <source src="${data.audio_url}" type="audio/mpeg">
                        <source src="${data.audio_url}" type="audio/wav">
                        Votre navigateur ne supporte pas la lecture audio.
                    </audio>
                    <div class="audio-info">
                        <small>⏱️ Durée: ${this.formatDuration(data.duration_seconds)} | 
                        🎯 Mots: ${data.keywords ? data.keywords.join(', ') : 'N/A'}</small>
                    </div>
                </div>
            `;
        } else if (data.result && data.result.audio_url) {
            this.setupP5AudioPlayer(data.result.audio_url, data.result);
            
            // Player de fallback
            audioPlayer.innerHTML = `
                <div class="audio-controls">
                    <h4>🎧 Écouter votre création :</h4>
                    <audio controls preload="auto" style="width: 100%; margin: 10px 0;">
                        <source src="${data.result.audio_url}" type="audio/mpeg">
                        <source src="${data.result.audio_url}" type="audio/wav">
                        Votre navigateur ne supporte pas la lecture audio.
                    </audio>
                    <div class="audio-info">
                        <small>⏱️ Durée: ${this.formatDuration(data.result.duration_seconds)} | 
                        🎯 Mots: ${data.result.keywords ? data.result.keywords.join(', ') : 'N/A'}</small>
                    </div>
                </div>
            `;
        } else {
            audioPlayer.innerHTML = '<p style="opacity: 0.7;">Audio non disponible</p>';
        }
        
        resultSection.classList.remove('hidden');
        
        // Scroll vers le résultat
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    setupP5AudioPlayer(audioUrl, metadata = {}) {
        console.log('🎧 Configuration du player p5.js...');
        
        // Attendre que p5.js et p5.sound soient complètement chargés
        const initP5Player = () => {
            try {
                // Vérifier que p5.js est bien chargé
                if (typeof p5 === 'undefined') {
                    console.error('❌ p5.js non chargé, fallback vers HTML5');
                    document.body.classList.add('no-p5');
                    return;
                }
                
                // p5.sound peut prendre du temps à s'initialiser
                if (typeof p5.Amplitude === 'undefined' || typeof p5.FFT === 'undefined') {
                    console.warn('⏳ p5.sound en cours de chargement, nouvelle tentative...');
                    setTimeout(initP5Player, 500); // Réessayer dans 500ms
                    return;
                }
                
                console.log('✅ p5.js et p5.sound chargés correctement');
                
                // Initialiser le visualisateur p5.js s'il n'existe pas encore
                if (typeof initAudioVisualizer === 'function' && !window.visualizer) {
                    const success = initAudioVisualizer();
                    if (!success) {
                        console.error('❌ Échec initialisation visualisateur');
                        document.body.classList.add('no-p5');
                        return;
                    }
                }
                
                // Ajouter à la playlist p5.js avec métadonnées complètes
                if (typeof addTrackToPlaylist === 'function') {
                    console.log('✅ Ajout à la playlist p5.js');
                    addTrackToPlaylist(audioUrl, {
                        phrases: metadata.phrases,
                        keywords: this.selectedWords,
                        duration_seconds: metadata.duration_seconds,
                        timestamp: new Date().toLocaleTimeString(),
                        love_analysis: metadata.love_analysis
                    });
                } else {
                    console.warn('addTrackToPlaylist non disponible, fallback vers loadAudioFile');
                    // Fallback vers l'ancienne méthode
                    if (typeof loadAudioFile === 'function') {
                        loadAudioFile(audioUrl);
                    }
                }
            } catch (error) {
                console.error('❌ Erreur initialisation player p5.js:', error);
                // Fallback vers le player HTML5
                document.body.classList.add('no-p5');
            }
        };
        
        // Démarrer l'initialisation
        initP5Player();
    }
    
    formatPhrases(phrases) {
        if (!phrases || phrases.length === 0) {
            return '<p>Aucune phrase générée</p>';
        }
        
        return phrases.map(phrase => `
            <div class="phrase-item">
                <div class="phrase-text">"${phrase.text}"</div>
                <div class="phrase-meta">
                    <span class="speaker">🎭 ${phrase.speaker}</span>
                    <span class="keywords">🎯 ${phrase.keywords_found.join(', ')}</span>
                    <span class="score">⭐ ${phrase.match_score.toFixed(1)}</span>
                </div>
            </div>
        `).join('');
    }
    
    formatDuration(seconds) {
        if (!seconds) return 'N/A';
        
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        
        if (mins > 0) {
            return `${mins}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
    
    formatPhraseOutput(output) {
        // Méthode de fallback pour l'ancien format
        if (typeof output === 'string') {
            return output.split('\\n').map(line => 
                line.trim() ? `<p>${line.trim()}</p>` : ''
            ).join('');
        }
        return '<p>Résultat généré avec succès!</p>';
    }
    
    showLoading() {
        document.getElementById('loading').classList.remove('hidden');
    }
    
    hideLoading() {
        document.getElementById('loading').classList.add('hidden');
    }
    
    showError(message) {
        // Simple alert pour le moment, peut être amélioré
        alert(`❌ ${message}`);
    }
    
    updateStatus(message) {
        const status = document.getElementById('status');
        if (status) {
            status.innerHTML = `<p>${message}</p>`;
        }
    }
    
    clearSelection() {
        this.selectedWords = [];
        
        // Désélectionner toutes les tuiles
        document.querySelectorAll('.word-tile.selected').forEach(tile => {
            tile.classList.remove('selected');
        });
        
        this.updateSelectedWordsDisplay();
        this.updateGenerateButton();
    }
    
    async refreshWords() {
        await this.loadRandomWords();
        this.clearSelection();
    }
    
    newCreation() {
        // Masquer le résultat
        document.getElementById('result').classList.add('hidden');
        
        // Actualiser les mots
        this.refreshWords();
    }
    
    attachEvents() {
        // Bouton générer
        document.getElementById('generate-btn').addEventListener('click', () => {
            this.generatePhrase();
        });
        
        // Bouton effacer
        document.getElementById('clear-selection').addEventListener('click', () => {
            this.clearSelection();
        });
        
        // Bouton nouveaux mots
        document.getElementById('refresh-words').addEventListener('click', () => {
            this.refreshWords();
        });
        
        // Bouton nouvelle création
        document.getElementById('new-creation').addEventListener('click', () => {
            this.newCreation();
        });
        
        // Prévenir le zoom sur double-tap mobile
        document.addEventListener('touchstart', (e) => {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        });
        
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (e) => {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // Gestion du redimensionnement
        window.addEventListener('resize', () => {
            if (window.resizeCanvas) {
                window.resizeCanvas();
            }
        });
    }
}

// Initialiser l'application au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    window.spectacleApp = new SpectacleApp();
});

// Gestion des erreurs globales
window.addEventListener('error', (e) => {
    console.error('❌ Erreur globale:', e.error);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('❌ Promise rejetée:', e.reason);
});

console.log('🎭 Script principal chargé');