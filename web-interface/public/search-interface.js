/* ===========================
   INTERFACE DE RECHERCHE DANS LES TRANSCRIPTIONS
   =========================== */

class SearchInterface {
    constructor() {
        this.searchInput = document.getElementById('searchInput');
        this.searchBtn = document.getElementById('searchBtn');
        this.resultsContainer = document.getElementById('results');
        this.loadingEl = document.getElementById('loading');
        this.searchInfoEl = document.getElementById('searchInfo');
        
        this.currentAudio = null;
        this.currentPlayBtn = null;
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Recherche au clic
        this.searchBtn.addEventListener('click', () => this.performSearch());
        
        // Recherche au Enter
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        // Focus automatique sur le champ de recherche
        this.searchInput.focus();
    }
    
    async performSearch() {
        const query = this.searchInput.value.trim();
        
        if (query.length < 2) {
            this.showError('Veuillez entrer au moins 2 caractères');
            return;
        }
        
        // Arrêter la lecture audio en cours
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }
        
        // Afficher le chargement
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
        this.resultsContainer.innerHTML = '';
        
        // Afficher les informations de recherche
        this.searchInfoEl.style.display = 'block';
        this.searchInfoEl.innerHTML = `
            Recherche pour <strong>"${data.query}"</strong> : 
            <strong>${data.total_results}</strong> résultat${data.total_results > 1 ? 's' : ''} trouvé${data.total_results > 1 ? 's' : ''}
            ${data.returned_results < data.total_results ? ` (affichage des ${data.returned_results} premiers)` : ''}
        `;
        
        if (data.results.length === 0) {
            this.showNoResults(data.query);
            return;
        }
        
        // Créer les cartes de résultats
        data.results.forEach((result, index) => {
            const card = this.createResultCard(result, index, data.query);
            this.resultsContainer.appendChild(card);
        });
    }
    
    createResultCard(result, index, query) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        // Formater le temps
        const startTime = this.formatTime(result.start_time);
        const endTime = this.formatTime(result.end_time);
        const duration = this.formatDuration(result.duration);
        
        // Extraire le nom du fichier sans extension
        const fileName = result.source_file.replace(/\.[^/.]+$/, '');
        
        // Surligner la requête dans le texte
        const highlightedText = this.highlightQuery(result.context_text, query);
        
        card.innerHTML = `
            <div class="result-header">
                <div class="source-info">
                    <span class="source-file">${fileName}</span>
                    <span class="time-info">${startTime} → ${endTime} (${duration})</span>
                </div>
                <span class="speaker-badge">${result.speaker}</span>
            </div>
            
            <div class="result-text">
                ${highlightedText}
            </div>
            
            <div class="result-footer">
                <div class="audio-player" data-result-index="${index}">
                    <button class="play-btn" data-audio-id="audio-${index}">▶</button>
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                    <div class="time-display">
                        <span class="current-time">0:00</span> / <span class="total-time">0:00</span>
                    </div>
                </div>
            </div>
        `;
        
        // Créer l'élément audio (masqué)
        const audio = new Audio();
        audio.id = `audio-${index}`;
        
        // Construire l'URL du fichier audio source
        const audioUrl = this.getAudioUrl(result.source_path);
        audio.src = audioUrl;
        
        // Configurer le temps de départ et de fin
        audio.dataset.startTime = result.start_time;
        audio.dataset.endTime = result.end_time;
        
        // Attacher les event listeners pour le player
        this.setupAudioPlayer(card, audio, index);
        
        return card;
    }
    
    getAudioUrl(sourcePath) {
        // Extraire le nom du fichier et construire l'URL relative
        const fileName = sourcePath.split('/').pop();
        
        // Détecter le sous-dossier (biotech, bop, cmu, etc.)
        let subFolder = '';
        if (sourcePath.includes('/biotech/')) subFolder = 'biotech';
        else if (sourcePath.includes('/bop/')) subFolder = 'bop';
        else if (sourcePath.includes('/cmu/')) subFolder = 'cmu';
        else if (sourcePath.includes('/fil/')) subFolder = 'fil';
        else if (sourcePath.includes('/mah/')) subFolder = 'mah';
        else if (sourcePath.includes('/contributions/')) subFolder = 'contributions';
        
        return `/audio-sources/${subFolder}/${fileName}`;
    }
    
    setupAudioPlayer(card, audio, index) {
        const playBtn = card.querySelector('.play-btn');
        const progressBar = card.querySelector('.progress-bar');
        const progressFill = card.querySelector('.progress-fill');
        const currentTimeEl = card.querySelector('.current-time');
        const totalTimeEl = card.querySelector('.total-time');
        
        const startTime = parseFloat(audio.dataset.startTime);
        const endTime = parseFloat(audio.dataset.endTime);
        const duration = endTime - startTime;
        
        // Afficher la durée totale
        totalTimeEl.textContent = this.formatDuration(duration);
        
        // Gestion du bouton play/pause
        playBtn.addEventListener('click', () => {
            if (audio.paused) {
                // Arrêter tout autre audio en cours
                if (this.currentAudio && this.currentAudio !== audio) {
                    this.currentAudio.pause();
                    if (this.currentPlayBtn) {
                        this.currentPlayBtn.textContent = '▶';
                    }
                }
                
                // Positionner au début de l'extrait
                audio.currentTime = startTime;
                audio.play();
                playBtn.textContent = '⏸';
                
                this.currentAudio = audio;
                this.currentPlayBtn = playBtn;
            } else {
                audio.pause();
                playBtn.textContent = '▶';
            }
        });
        
        // Mise à jour de la barre de progression
        audio.addEventListener('timeupdate', () => {
            const relativeTime = audio.currentTime - startTime;
            const progress = (relativeTime / duration) * 100;
            
            progressFill.style.width = `${Math.min(progress, 100)}%`;
            currentTimeEl.textContent = this.formatDuration(Math.max(0, relativeTime));
            
            // Arrêter à la fin de l'extrait
            if (audio.currentTime >= endTime) {
                audio.pause();
                audio.currentTime = startTime;
                playBtn.textContent = '▶';
                progressFill.style.width = '0%';
                currentTimeEl.textContent = '0:00';
            }
        });
        
        // Réinitialiser à la fin
        audio.addEventListener('ended', () => {
            audio.currentTime = startTime;
            playBtn.textContent = '▶';
            progressFill.style.width = '0%';
            currentTimeEl.textContent = '0:00';
        });
        
        // Gestion du clic sur la barre de progression
        progressBar.addEventListener('click', (e) => {
            const rect = progressBar.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            audio.currentTime = startTime + (duration * percent);
        });
        
        // Gestion des erreurs de chargement
        audio.addEventListener('error', (e) => {
            console.error('Erreur chargement audio:', audio.src, e);
            playBtn.disabled = true;
            playBtn.textContent = '✕';
            playBtn.style.opacity = '0.5';
        });
    }
    
    highlightQuery(text, query) {
        // Échapper les caractères spéciaux de regex
        const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        
        // Créer une regex insensible à la casse
        const regex = new RegExp(`(${escapedQuery})`, 'gi');
        
        // Remplacer en préservant la casse originale
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
        this.loadingEl.style.display = 'block';
        this.resultsContainer.innerHTML = '';
        this.searchInfoEl.style.display = 'none';
    }
    
    hideLoading() {
        this.loadingEl.style.display = 'none';
    }
    
    showError(message) {
        this.resultsContainer.innerHTML = `
            <div class="error-message">
                <strong>Erreur :</strong> ${message}
            </div>
        `;
        this.searchInfoEl.style.display = 'none';
    }
    
    showNoResults(query) {
        this.resultsContainer.innerHTML = `
            <div class="no-results">
                <h3>Aucun résultat trouvé</h3>
                <p>Aucune transcription ne contient "${query}".</p>
                <p>Essayez avec d'autres mots-clés.</p>
            </div>
        `;
    }
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    new SearchInterface();
});
