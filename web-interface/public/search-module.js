/* ===========================
   MODULE DE RECHERCHE - VERSION INTÉGRÉE
   Style minimaliste noir et blanc
   =========================== */

class SearchModule {
    constructor() {
        this.panel = document.getElementById('search-panel');
        this.searchInput = document.getElementById('search-input');
        this.searchResults = document.getElementById('search-results');
        this.searchInfo = document.getElementById('search-info');
        this.searchLoading = document.getElementById('search-loading');
        this.closeBtn = document.getElementById('close-search');
        
        this.currentAudio = null;
        this.currentPlayBtn = null;
        this.currentTextContainer = null; // Pour l'animation karaoké
        this.animationFrameId = null; // Pour optimiser l'animation
        this.isOpen = false;
        
        this.init();
    }
    
    init() {
        // Événement pour le bouton de recherche dans la nav
        const searchBtn = document.querySelector('[data-action="search"]');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.open());
        }
        
        // Fermeture
        this.closeBtn.addEventListener('click', () => this.close());
        
        // Recherche au Enter
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        // Recherche automatique après 500ms d'inactivité
        let searchTimeout;
        this.searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.searchInput.value.trim().length >= 2) {
                    this.performSearch();
                }
            }, 500);
        });
        
        console.log('🔍 Module de recherche initialisé');
    }
    
    open() {
        this.panel.classList.add('open');
        this.isOpen = true;
        
        // Focus sur le champ de recherche
        setTimeout(() => {
            this.searchInput.focus();
        }, 300);
    }
    
    close() {
        this.panel.classList.remove('open');
        this.isOpen = false;
        
        // Arrêter la lecture audio en cours
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }
        
        // Annuler toute animation en cours
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }
    
    async performSearch() {
        const query = this.searchInput.value.trim();
        
        if (query.length < 2) {
            this.showError('Veuillez entrer au moins 2 caractères');
            return;
        }
        
        // Arrêter tout audio en cours
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }
        
        this.showLoading();
        
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Erreur lors de la recherche');
            }
            
            this.displayResults(data);
            
        } catch (error) {
            console.error('Erreur recherche:', error);
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    displayResults(data) {
        this.searchResults.innerHTML = '';
        
        // Afficher les informations
        this.searchInfo.style.display = 'block';
        this.searchInfo.textContent = `${data.total_results} résultat${data.total_results > 1 ? 's' : ''} trouvé${data.total_results > 1 ? 's' : ''}`;
        
        if (data.results.length === 0) {
            this.showNoResults(data.query);
            return;
        }
        
        // Créer les résultats
        data.results.forEach((result, index) => {
            const resultEl = this.createResultElement(result, index, data.query);
            this.searchResults.appendChild(resultEl);
        });
    }
    
    createResultElement(result, index, query) {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'search-result';
        
        // Formater les temps
        const startTime = this.formatTime(result.start_time);
        const endTime = this.formatTime(result.end_time);
        const duration = this.formatDuration(result.duration);
        
        // Nom du fichier sans extension
        const fileName = result.source_file.replace(/\.[^/.]+$/, '');
        
        resultDiv.innerHTML = `
            <div class="result-header">
                <div class="result-source">${fileName}</div>
                <div class="result-speaker">${result.speaker}</div>
            </div>
            <div class="result-text" data-result-index="${index}"></div>
            <div class="result-footer">
                <div class="result-time">${startTime} → ${endTime} (${duration})</div>
                <div class="result-player">
                    <button class="result-play-btn" data-result-index="${index}"><span class="play-symbol">▶</span></button>
                    <button class="result-download-btn" data-result-index="${index}" title="Télécharger cet extrait">↓</button>
                </div>
            </div>
        `;
        
        // Créer l'affichage karaoké du texte
        const textContainer = resultDiv.querySelector('.result-text');
        this.renderKaraokeText(textContainer, result, query);
        
        // Stocker les mots karaoké pour optimiser l'animation
        textContainer._karaokeWords = textContainer.querySelectorAll('.karaoke-word');
        
        // Configuration du player
        const playBtn = resultDiv.querySelector('.result-play-btn');
        this.setupPlayer(playBtn, result, textContainer);
        
        // Configuration du téléchargement
        const downloadBtn = resultDiv.querySelector('.result-download-btn');
        this.setupDownload(downloadBtn, result);
        
        return resultDiv;
    }
    
    renderKaraokeText(container, result, query) {
        container.innerHTML = '';
        
        // Vérifier si on a des données word-level dans les segments
        const segments = result.context_segments || [];
        let hasWordData = false;
        
        segments.forEach((segment, segIndex) => {
            if (segment.words && segment.words.length > 0) {
                hasWordData = true;
                
                // Créer un span pour chaque mot
                segment.words.forEach((wordObj, wordIndex) => {
                    const wordSpan = document.createElement('span');
                    wordSpan.className = 'karaoke-word';
                    wordSpan.textContent = wordObj.word;
                    wordSpan.setAttribute('data-segment', segIndex);
                    wordSpan.setAttribute('data-word', wordIndex);
                    wordSpan.setAttribute('data-start', wordObj.start);
                    wordSpan.setAttribute('data-end', wordObj.end);
                    
                    // Surligner si c'est le mot recherché
                    if (query && wordObj.word.toLowerCase().includes(query.toLowerCase())) {
                        wordSpan.style.fontWeight = '400';
                        wordSpan.style.opacity = '1';
                    }
                    
                    container.appendChild(wordSpan);
                });
                
                // Ajouter un espace entre les segments
                if (segIndex < segments.length - 1) {
                    const space = document.createTextNode(' ');
                    container.appendChild(space);
                }
            } else {
                // Pas de données word-level, afficher le texte normal
                const text = this.highlightQuery(segment.text, query);
                const textSpan = document.createElement('span');
                textSpan.innerHTML = text;
                container.appendChild(textSpan);
                
                if (segIndex < segments.length - 1) {
                    const space = document.createTextNode(' ');
                    container.appendChild(space);
                }
            }
        });
        
        // Si pas de segments ou pas de données word-level, fallback sur le texte complet
        if (!hasWordData && segments.length === 0) {
            const text = this.highlightQuery(result.context_text, query);
            container.innerHTML = text;
        }
    }
    
    setupPlayer(playBtn, result, textContainer) {
        const audio = new Audio();
        const audioUrl = this.getAudioUrl(result.source_path);
        audio.src = audioUrl;
        
        const startTime = result.start_time;
        const endTime = result.end_time;
        
        playBtn.addEventListener('click', () => {
            if (audio.paused) {
                // Arrêter tout autre audio
                if (this.currentAudio && this.currentAudio !== audio) {
                    this.currentAudio.pause();
                    if (this.currentPlayBtn) {
                        this.currentPlayBtn.innerHTML = '<span class="play-symbol">▶</span>';
                        this.currentPlayBtn.classList.remove('playing');
                    }
                    // Réinitialiser l'animation karaoké du précédent
                    if (this.currentTextContainer && this.currentTextContainer._karaokeWords) {
                        this.currentTextContainer._karaokeWords.forEach(w => w.classList.remove('active'));
                    }
                    // Annuler l'animation frame en cours
                    if (this.animationFrameId) {
                        cancelAnimationFrame(this.animationFrameId);
                        this.animationFrameId = null;
                    }
                }
                
                // Démarrer la lecture
                audio.currentTime = startTime;
                audio.play();
                playBtn.innerHTML = '<span class="play-symbol">❙❙</span>';
                playBtn.classList.add('playing');
                
                this.currentAudio = audio;
                this.currentPlayBtn = playBtn;
                this.currentTextContainer = textContainer;
            } else {
                audio.pause();
                playBtn.innerHTML = '<span class="play-symbol">▶</span>';
                playBtn.classList.remove('playing');
                
                // Annuler l'animation frame
                if (this.animationFrameId) {
                    cancelAnimationFrame(this.animationFrameId);
                    this.animationFrameId = null;
                }
            }
        });
        
        // Animation karaoké avec requestAnimationFrame pour optimiser
        let lastUpdateTime = 0;
        const updateInterval = 100; // Mise à jour max toutes les 100ms
        
        audio.addEventListener('timeupdate', () => {
            const now = Date.now();
            
            // Throttle: ne mettre à jour que toutes les 100ms
            if (now - lastUpdateTime < updateInterval) {
                return;
            }
            lastUpdateTime = now;
            
            // Utiliser requestAnimationFrame pour l'animation
            if (this.animationFrameId) {
                cancelAnimationFrame(this.animationFrameId);
            }
            
            this.animationFrameId = requestAnimationFrame(() => {
                this.animateResultKaraoke(audio.currentTime, textContainer);
            });
            
            // Arrêter à la fin de l'extrait
            if (audio.currentTime >= endTime) {
                audio.pause();
                audio.currentTime = startTime;
                playBtn.innerHTML = '<span class="play-symbol">▶</span>';
                playBtn.classList.remove('playing');
                
                // Réinitialiser l'animation karaoké
                if (textContainer._karaokeWords) {
                    textContainer._karaokeWords.forEach(w => w.classList.remove('active'));
                }
                
                if (this.animationFrameId) {
                    cancelAnimationFrame(this.animationFrameId);
                    this.animationFrameId = null;
                }
            }
        });
        
        // Gestion des erreurs
        audio.addEventListener('error', () => {
            playBtn.disabled = true;
            playBtn.innerHTML = '<span class="play-symbol">✕</span>';
            playBtn.style.opacity = '0.3';
        });
    }
    
    animateResultKaraoke(currentTime, textContainer) {
        // Utiliser les mots pré-stockés pour éviter querySelectorAll
        const words = textContainer._karaokeWords;
        
        if (!words || words.length === 0) return;
        
        // Optimisation: ne parcourir que les mots visibles
        words.forEach(word => {
            const start = parseFloat(word.dataset.start);
            const end = parseFloat(word.dataset.end);
            
            if (currentTime >= start && currentTime <= end) {
                if (!word.classList.contains('active')) {
                    word.classList.add('active');
                }
            } else {
                if (word.classList.contains('active')) {
                    word.classList.remove('active');
                }
            }
        });
    }
    
    getAudioUrl(sourcePath) {
        const fileName = sourcePath.split('/').pop();
        
        // Détecter le sous-dossier
        let subFolder = '';
        if (sourcePath.includes('/biotech/')) subFolder = 'biotech';
        else if (sourcePath.includes('/bop/')) subFolder = 'bop';
        else if (sourcePath.includes('/cmu/')) subFolder = 'cmu';
        else if (sourcePath.includes('/fil/')) subFolder = 'fil';
        else if (sourcePath.includes('/mah/')) subFolder = 'mah';
        else if (sourcePath.includes('/contributions/')) subFolder = 'contributions';
        
        return `/audio-sources/${subFolder}/${fileName}`;
    }
    
    setupDownload(btn, result) {
        btn.addEventListener('click', async () => {
            try {
                // Afficher l'indicateur de chargement
                const originalContent = btn.innerHTML;
                btn.innerHTML = '⏳';
                btn.disabled = true;
                
                // Demander l'extraction du segment audio
                const response = await fetch('/api/extract-search-audio', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        audio_path: result.source_path,
                        start_time: result.start_time,
                        end_time: result.end_time
                    })
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Erreur lors de l\'extraction audio');
                }
                
                const data = await response.json();
                
                if (!data.success || !data.audio_file) {
                    throw new Error(data.error || 'Aucun fichier audio généré');
                }
                
                // Télécharger le fichier
                const link = document.createElement('a');
                link.href = `/audio/${data.audio_file}`;
                link.download = data.audio_file;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                // Feedback visuel de succès
                btn.innerHTML = '✓';
                btn.disabled = false;
                setTimeout(() => {
                    btn.innerHTML = originalContent;
                }, 1500);
                
            } catch (error) {
                console.error('Erreur téléchargement:', error);
                btn.innerHTML = '✕';
                btn.disabled = false;
                setTimeout(() => {
                    btn.innerHTML = '↓';
                    btn.disabled = false;
                }, 2000);
            }
        });
    }
    
    highlightQuery(text, query) {
        const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedQuery})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }
    
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    showLoading() {
        this.searchLoading.style.display = 'block';
        this.searchResults.innerHTML = '';
        this.searchInfo.style.display = 'none';
    }
    
    hideLoading() {
        this.searchLoading.style.display = 'none';
    }
    
    showError(message) {
        this.searchResults.innerHTML = `
            <div class="no-results">
                <h3>erreur</h3>
                <p>${message}</p>
            </div>
        `;
        this.searchInfo.style.display = 'none';
    }
    
    showNoResults(query) {
        this.searchResults.innerHTML = `
            <div class="no-results">
                <h3>aucun résultat</h3>
                <p>Aucune transcription ne contient "${query}"</p>
                <p>Essayez avec d'autres mots</p>
            </div>
        `;
    }
}

// Initialisation après le chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    // Attendre que PoeticInterface soit initialisé
    setTimeout(() => {
        window.searchModule = new SearchModule();
    }, 100);
});
