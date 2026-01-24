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
                await this.displayResult(data);
                
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
    
    async displayResult(data) {
        const resultSection = document.getElementById('result');
        const phraseOutput = document.getElementById('phrase-output');
        // Plus besoin d'audioPlayer - utilisation de la nouvelle interface modulaire
        
        // Afficher les phrases générées
        if (data.phrases && data.phrases.length > 0) {
            phraseOutput.innerHTML = this.formatPhrases(data.phrases);
        } else if (data.result && data.result.phrases) {
            phraseOutput.innerHTML = this.formatPhrases(data.result.phrases);
        } else {
            phraseOutput.innerHTML = '<p>Phrases générées avec succès!</p>';
        }
        
        // Utiliser la nouvelle interface audio modulaire
        if (data.audio_url) {
            await this.setupP5AudioPlayer(data.audio_url, data);
        } else if (data.result && data.result.audio_url) {
            await this.setupP5AudioPlayer(data.result.audio_url, data.result);
        } else {
            console.warn('⚠️ Aucun audio disponible dans la réponse');
        }
        
        resultSection.classList.remove('hidden');
        
        // Scroll vers le résultat
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    async setupP5AudioPlayer(audioUrl, metadata = {}) {
        console.log('🎧 Configuration du nouveau player modulaire...');
        
        try {
            // Utiliser la nouvelle interface audio modulaire
            if (typeof initializeNewAudioInterface === 'function') {
                
                // Initialiser l'interface si pas déjà fait
                if (!window.audioInterface) {
                    window.audioInterface = await initializeNewAudioInterface();
                }
                
                // Ajouter le track avec toutes les métadonnées
                const trackId = window.audioInterface.addTrack(audioUrl, {
                    phrases: metadata.phrases,
                    keywords: this.selectedWords,
                    duration_seconds: metadata.duration_seconds,
                    timestamp: new Date().toLocaleTimeString(),
                    love_analysis: metadata.love_analysis,
                    title: metadata.title || this.extractPhraseTitle(metadata)
                });
                
                console.log(`✅ Track ajouté avec ID: ${trackId}`);
                
            } else {
                console.warn('⚠️ Interface audio modulaire non disponible, fallback HTML5');
                // Fallback vers player HTML5 simple
                this.createFallbackPlayer(audioUrl, metadata);
            }
            
        } catch (error) {
            console.error('❌ Erreur configuration player:', error);
            this.createFallbackPlayer(audioUrl, metadata);
        }
    }
    
    extractPhraseTitle(metadata) {
        if (metadata.phrases && metadata.phrases.length > 0) {
            return metadata.phrases[0].text.substring(0, 50) + '...';
        }
        return `Phrase ${this.selectedWords.join(', ')} - ${new Date().toLocaleTimeString()}`;
    }
    
    createFallbackPlayer(audioUrl, metadata) {
        // Player de fallback simple dans le container de l'interface modulaire
        const audioInterfaceContainer = document.getElementById('audio-interface-container');
        if (audioInterfaceContainer) {
            audioInterfaceContainer.innerHTML = `
                <div class="fallback-audio-player">
                    <h4>🎧 Écouter votre création :</h4>
                    <audio controls preload="auto" style="width: 100%; margin: 10px 0;">
                        <source src="${audioUrl}" type="audio/mpeg">
                        <source src="${audioUrl}" type="audio/wav">
                        Votre navigateur ne supporte pas la lecture audio.
                    </audio>
                    <div class="audio-info">
                        <p><strong>Mots-clés:</strong> ${this.selectedWords.join(', ')}</p>
                        ${metadata.duration_seconds ? `<p><strong>Durée:</strong> ${this.formatDuration(metadata.duration_seconds)}</p>` : ''}
                        <p><strong>Généré le:</strong> ${new Date().toLocaleTimeString()}</p>
                    </div>
                </div>
            `;
        } else {
            console.warn('⚠️ Container audio-interface-container non trouvé');
        }
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
            // Redimensionnement géré par les composants modulaires
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