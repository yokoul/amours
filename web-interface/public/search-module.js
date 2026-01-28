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
        this.contextDurationSlider = document.getElementById('context-duration-slider');
        this.contextDurationValue = document.getElementById('context-duration-value');
        
        this.currentAudio = null;
        this.currentPlayBtn = null;
        this.currentTextContainer = null; // Pour l'animation karaoké
        this.animationFrameId = null; // Pour optimiser l'animation
        this.audioCache = new Map(); // Cache des extraits audio générés
        this.isOpen = false;
        
        // Pagination
        this.currentPage = 1;
        this.resultsPerPage = 10;
        this.totalResults = 0;
        this.currentQuery = '';
        
        // Filtres
        this.availableSources = [];
        this.selectedSources = new Set(); // Ensemble des sources sélectionnées
        
        // Durée du contexte (en secondes)
        this.contextDuration = 60;
        
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
        
        // Recherche uniquement au Enter
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.currentPage = 1; // Réinitialiser à la page 1
                this.performSearch();
            }
        });
        
        // Gestion du slider de durée
        if (this.contextDurationSlider) {
            this.contextDurationSlider.addEventListener('input', (e) => {
                this.contextDuration = parseInt(e.target.value);
                this.contextDurationValue.textContent = this.contextDuration;
            });
            
            // Déclencher une recherche si une recherche était en cours
            this.contextDurationSlider.addEventListener('change', () => {
                if (this.currentQuery) {
                    this.currentPage = 1;
                    this.performSearch();
                }
            });
        }
        
        // Gestion du bouton filtre/reset
        const filterToggleBtn = document.getElementById('filter-toggle-btn');
        if (filterToggleBtn) {
            filterToggleBtn.addEventListener('click', () => {
                if (filterToggleBtn.classList.contains('reset-mode')) {
                    // Mode reset : réinitialiser tout
                    this.resetSearch();
                } else {
                    // Mode filtre : basculer l'affichage des filtres
                    this.toggleFilters();
                    
                    // Mettre à jour l'icône
                    const filtersPanel = document.getElementById('search-filters');
                    if (filtersPanel && filtersPanel.classList.contains('open')) {
                        filterToggleBtn.textContent = '×';
                    } else {
                        filterToggleBtn.textContent = '⚙︎';
                    }
                }
            });
        }
        
        console.log('🔍 Module de recherche initialisé');
    }
    
    async open() {
        this.panel.classList.add('open');
        this.isOpen = true;
        
        // Charger les sources disponibles si ce n'est pas déjà fait
        if (this.availableSources.length === 0) {
            await this.loadAvailableSources();
        }
        
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
    
    toggleFilters() {
        const filtersPanel = document.getElementById('search-filters');
        if (filtersPanel) {
            filtersPanel.classList.toggle('open');
        }
    }
    
    resetSearch() {
        // Réinitialiser le champ de recherche
        this.searchInput.value = '';
        
        // Effacer les résultats
        this.searchResults.innerHTML = '';
        this.searchInfo.style.display = 'none';
        
        // Réinitialiser les filtres
        this.selectedSources.clear();
        const checkboxes = document.querySelectorAll('.source-filter-item input[type="checkbox"]');
        checkboxes.forEach(cb => cb.checked = false);
        
        // Réinitialiser l'état
        this.currentPage = 1;
        this.totalResults = 0;
        this.currentQuery = '';
        
        // Remettre le bouton en mode filtre
        const filterToggleBtn = document.getElementById('filter-toggle-btn');
        if (filterToggleBtn) {
            filterToggleBtn.classList.remove('reset-mode');
            filterToggleBtn.textContent = '⚙︎';
            filterToggleBtn.title = 'Filtrer par source';
        }
        
        // Mettre à jour le texte du bouton toggle all
        const toggleAllBtn = document.querySelector('.filter-toggle-all');
        if (toggleAllBtn) {
            toggleAllBtn.textContent = 'tout sélectionner';
        }
        
        // Focus sur le champ de recherche
        this.searchInput.focus();
    }
    
    async loadAvailableSources() {
        try {
            const response = await fetch('/api/search-sources');
            const data = await response.json();
            
            if (data.success && data.sources) {
                this.availableSources = data.sources;
                this.renderSourceFilters();
            }
        } catch (error) {
            console.error('Erreur chargement sources:', error);
        }
    }
    
    renderSourceFilters() {
        const filterContainer = document.getElementById('source-filters');
        if (!filterContainer) return;
        
        filterContainer.innerHTML = '';
        
        // Bouton "Tout sélectionner / Tout désélectionner"
        const toggleAllBtn = document.createElement('button');
        toggleAllBtn.className = 'filter-toggle-all';
        toggleAllBtn.textContent = 'tout sélectionner';
        toggleAllBtn.addEventListener('click', () => {
            if (this.selectedSources.size === this.availableSources.length) {
                // Tout désélectionner
                this.selectedSources.clear();
                toggleAllBtn.textContent = 'tout sélectionner';
                filterContainer.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            } else {
                // Tout sélectionner
                this.availableSources.forEach(source => this.selectedSources.add(source));
                toggleAllBtn.textContent = 'tout désélectionner';
                filterContainer.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
            }
            this.updateFilterButtonState();
        });
        filterContainer.appendChild(toggleAllBtn);
        
        // Liste des sources
        const sourceList = document.createElement('div');
        sourceList.className = 'source-list';
        
        this.availableSources.forEach(source => {
            const label = document.createElement('label');
            label.className = 'source-filter-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = source;
            checkbox.checked = this.selectedSources.has(source);
            checkbox.addEventListener('change', (e) => {
                // Déployer automatiquement si replié
                const searchFilters = document.getElementById('search-filters');
                const filterToggleBtn = document.getElementById('filter-toggle-btn');
                if (searchFilters && searchFilters.classList.contains('collapsed')) {
                    searchFilters.classList.remove('collapsed');
                    if (filterToggleBtn) filterToggleBtn.classList.add('active');
                }
                
                if (e.target.checked) {
                    this.selectedSources.add(source);
                } else {
                    this.selectedSources.delete(source);
                }
                
                // Mettre à jour le bouton toggle
                if (this.selectedSources.size === this.availableSources.length) {
                    toggleAllBtn.textContent = 'tout désélectionner';
                } else {
                    toggleAllBtn.textContent = 'tout sélectionner';
                }
                
                this.updateFilterButtonState();
            });
            
            const span = document.createElement('span');
            span.textContent = source;
            
            label.appendChild(checkbox);
            label.appendChild(span);
            sourceList.appendChild(label);
        });
        
        filterContainer.appendChild(sourceList);
    }
    
    updateFilterButtonState() {
        const filterToggleBtn = document.getElementById('filter-toggle-btn');
        if (!filterToggleBtn) return;
        
        // Mettre en évidence si des filtres sont actifs
        if (this.selectedSources.size > 0 && this.selectedSources.size < this.availableSources.length) {
            filterToggleBtn.style.opacity = '1';
            filterToggleBtn.style.borderColor = 'var(--black)';
        } else {
            filterToggleBtn.style.opacity = '';
            filterToggleBtn.style.borderColor = '';
        }
    }
    
    async performSearch(page = null) {
        const query = this.searchInput.value.trim();
        
        if (query.length < 2) {
            this.showError('Veuillez entrer au moins 2 caractères');
            return;
        }
        
        // Si nouvelle requête, réinitialiser la page
        if (query !== this.currentQuery) {
            this.currentPage = 1;
            this.currentQuery = query;
        }
        
        // Si page spécifiée, l'utiliser
        if (page !== null) {
            this.currentPage = page;
        }
        
        // Arrêter tout audio en cours
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }
        
        this.showLoading();
        
        try {
            const offset = (this.currentPage - 1) * this.resultsPerPage;
            let url = `/api/search?q=${encodeURIComponent(query)}&limit=${this.resultsPerPage}&offset=${offset}`;
            
            // Ajouter la durée du contexte
            url += `&context_duration=${this.contextDuration}`;
            
            // Ajouter les sources sélectionnées
            if (this.selectedSources.size > 0 && this.selectedSources.size < this.availableSources.length) {
                const sources = Array.from(this.selectedSources).join(',');
                url += `&sources=${encodeURIComponent(sources)}`;
            }
            
            const response = await fetch(url);
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Erreur lors de la recherche');
            }
            
            this.totalResults = data.total_results;
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
        
        // Afficher les informations avec pagination
        const totalPages = Math.ceil(this.totalResults / this.resultsPerPage);
        const startResult = (this.currentPage - 1) * this.resultsPerPage + 1;
        const endResult = Math.min(this.currentPage * this.resultsPerPage, this.totalResults);
        
        this.searchInfo.style.display = 'block';
        this.searchInfo.textContent = `${this.totalResults} résultat${this.totalResults > 1 ? 's' : ''} trouvé${this.totalResults > 1 ? 's' : ''} · Affichage ${startResult}-${endResult}`;
        
        // Activer le mode reset sur le bouton
        const filterToggleBtn = document.getElementById('filter-toggle-btn');
        if (filterToggleBtn) {
            filterToggleBtn.classList.add('reset-mode');
            filterToggleBtn.textContent = '↺';
            filterToggleBtn.title = 'Réinitialiser la recherche';
        }
        
        if (data.results.length === 0) {
            this.showNoResults(data.query);
            return;
        }
        
        // Créer les résultats
        data.results.forEach((result, index) => {
            const resultEl = this.createResultElement(result, index, data.query);
            this.searchResults.appendChild(resultEl);
        });
        
        // Ajouter la pagination si nécessaire
        if (totalPages > 1) {
            this.addPagination(totalPages);
        }
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
        // Créer une clé de cache unique pour cet extrait
        const cacheKey = `${result.source_path}_${result.start_time}_${result.end_time}`;
        
        const startTime = result.start_time;
        const endTime = result.end_time;
        
        playBtn.addEventListener('click', async () => {
            if (!playBtn._audio || playBtn._audio.paused) {
                // Arrêter tout autre audio
                if (this.currentAudio && this.currentAudio !== playBtn._audio) {
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
                
                // Désactiver le bouton pendant le chargement
                playBtn.disabled = true;
                const originalContent = playBtn.innerHTML;
                playBtn.innerHTML = '<span class="play-symbol">⏳</span>';
                
                try {
                    // Vérifier le cache d'abord
                    let audioUrl;
                    if (this.audioCache.has(cacheKey)) {
                        audioUrl = this.audioCache.get(cacheKey);
                    } else {
                        // Extraire le segment audio via l'API
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
                            throw new Error('Erreur lors de l\'extraction audio');
                        }
                        
                        const data = await response.json();
                        if (!data.success || !data.audio_file) {
                            throw new Error('Aucun fichier audio généré');
                        }
                        
                        audioUrl = `/audio/${data.audio_file}`;
                        this.audioCache.set(cacheKey, audioUrl);
                    }
                    
                    // Créer ou réutiliser l'objet Audio
                    if (!playBtn._audio) {
                        playBtn._audio = new Audio();
                        playBtn._audio.src = audioUrl;
                        
                        // Animation karaoké avec requestAnimationFrame
                        let lastUpdateTime = 0;
                        const updateInterval = 100;
                        
                        playBtn._audio.addEventListener('timeupdate', () => {
                            const now = Date.now();
                            
                            if (now - lastUpdateTime < updateInterval) {
                                return;
                            }
                            lastUpdateTime = now;
                            
                            if (this.animationFrameId) {
                                cancelAnimationFrame(this.animationFrameId);
                            }
                            
                            this.animationFrameId = requestAnimationFrame(() => {
                                // Ajuster le temps pour correspondre à la transcription complète
                                const adjustedTime = playBtn._audio.currentTime + startTime;
                                this.animateResultKaraoke(adjustedTime, textContainer);
                            });
                        });
                        
                        // Fin de lecture
                        playBtn._audio.addEventListener('ended', () => {
                            playBtn.innerHTML = '<span class="play-symbol">▶</span>';
                            playBtn.classList.remove('playing');
                            
                            if (textContainer._karaokeWords) {
                                textContainer._karaokeWords.forEach(w => w.classList.remove('active'));
                            }
                            
                            if (this.animationFrameId) {
                                cancelAnimationFrame(this.animationFrameId);
                                this.animationFrameId = null;
                            }
                        });
                        
                        playBtn._audio.addEventListener('error', () => {
                            playBtn.disabled = true;
                            playBtn.innerHTML = '<span class="play-symbol">✕</span>';
                            playBtn.style.opacity = '0.3';
                        });
                    }
                    
                    // Démarrer la lecture
                    playBtn._audio.currentTime = 0;
                    await playBtn._audio.play();
                    playBtn.innerHTML = '<span class="play-symbol">❙❙</span>';
                    playBtn.classList.add('playing');
                    playBtn.disabled = false;
                    
                    this.currentAudio = playBtn._audio;
                    this.currentPlayBtn = playBtn;
                    this.currentTextContainer = textContainer;
                    
                } catch (error) {
                    console.error('Erreur lecture audio:', error);
                    playBtn.innerHTML = originalContent;
                    playBtn.disabled = false;
                    alert('Impossible de lire cet extrait audio');
                }
                
            } else {
                // Mettre en pause
                playBtn._audio.pause();
                playBtn.innerHTML = '<span class="play-symbol">▶</span>';
                playBtn.classList.remove('playing');
                
                if (this.animationFrameId) {
                    cancelAnimationFrame(this.animationFrameId);
                    this.animationFrameId = null;
                }
            }
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
    
    addPagination(totalPages) {
        const paginationDiv = document.createElement('div');
        paginationDiv.className = 'search-pagination';
        
        // Bouton précédent
        const prevBtn = document.createElement('button');
        prevBtn.className = 'pagination-btn';
        prevBtn.textContent = '‹ Précédent';
        prevBtn.disabled = this.currentPage === 1;
        prevBtn.addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.performSearch(this.currentPage - 1);
                this.searchResults.scrollTop = 0;
            }
        });
        paginationDiv.appendChild(prevBtn);
        
        // Indicateur de page
        const pageInfo = document.createElement('span');
        pageInfo.className = 'pagination-info';
        pageInfo.textContent = `Page ${this.currentPage} / ${totalPages}`;
        paginationDiv.appendChild(pageInfo);
        
        // Bouton suivant
        const nextBtn = document.createElement('button');
        nextBtn.className = 'pagination-btn';
        nextBtn.textContent = 'Suivant ›';
        nextBtn.disabled = this.currentPage === totalPages;
        nextBtn.addEventListener('click', () => {
            if (this.currentPage < totalPages) {
                this.performSearch(this.currentPage + 1);
                this.searchResults.scrollTop = 0;
            }
        });
        paginationDiv.appendChild(nextBtn);
        
        this.searchResults.appendChild(paginationDiv);
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
