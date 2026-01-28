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
        
        // Surligner la requête
        const highlightedText = this.highlightQuery(result.context_text, query);
        
        resultDiv.innerHTML = `
            <div class="result-header">
                <div class="result-source">${fileName}</div>
                <div class="result-speaker">${result.speaker}</div>
            </div>
            <div class="result-text">${highlightedText}</div>
            <div class="result-footer">
                <div class="result-time">${startTime} → ${endTime} (${duration})</div>
                <div class="result-player">
                    <button class="result-play-btn" data-result-index="${index}">▶</button>
                    <button class="result-download-btn" data-result-index="${index}" title="Télécharger cet extrait">⬇</button>
                </div>
            </div>
        `;
        
        // Configuration du player
        const playBtn = resultDiv.querySelector('.result-play-btn');
        this.setupPlayer(playBtn, result);
        
        // Configuration du téléchargement
        const downloadBtn = resultDiv.querySelector('.result-download-btn');
        this.setupDownload(downloadBtn, result);
        
        return resultDiv;
    }
    
    setupPlayer(playBtn, result) {
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
                        this.currentPlayBtn.textContent = '▶';
                        this.currentPlayBtn.classList.remove('playing');
                    }
                }
                
                // Démarrer la lecture
                audio.currentTime = startTime;
                audio.play();
                playBtn.textContent = '⏸';
                playBtn.classList.add('playing');
                
                this.currentAudio = audio;
                this.currentPlayBtn = playBtn;
            } else {
                audio.pause();
                playBtn.textContent = '▶';
                playBtn.classList.remove('playing');
            }
        });
        
        // Arrêter à la fin de l'extrait
        audio.addEventListener('timeupdate', () => {
            if (audio.currentTime >= endTime) {
                audio.pause();
                audio.currentTime = startTime;
                playBtn.textContent = '▶';
                playBtn.classList.remove('playing');
            }
        });
        
        // Gestion des erreurs
        audio.addEventListener('error', () => {
            playBtn.disabled = true;
            playBtn.textContent = '✕';
            playBtn.style.opacity = '0.3';
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
                    btn.innerHTML = '⬇';
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
