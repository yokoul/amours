// Player audio HTML5 simple avec playlist
class HTML5AudioPlayer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.playlist = [];
        this.currentTrackIndex = -1;
        this.audio = null;
        this.isPlaying = false;
        
        this.init();
    }
    
    init() {
        this.createPlayerUI();
        this.attachEvents();
        console.log('🎧 Player HTML5 initialisé');
    }
    
    createPlayerUI() {
        this.container.innerHTML = `
            <div class="html5-player">
                <div class="player-controls">
                    <button id="prev-btn" class="control-btn" disabled>⏮</button>
                    <button id="play-btn" class="control-btn play-btn" disabled>▶</button>
                    <button id="next-btn" class="control-btn" disabled>⏭</button>
                </div>
                
                <div class="track-info">
                    <div class="track-title">Aucun audio chargé</div>
                    <div class="track-meta"></div>
                </div>
                
                <div class="progress-container">
                    <div class="time-current">0:00</div>
                    <div class="progress-bar">
                        <div class="progress-track">
                            <div class="progress-fill"></div>
                            <div class="progress-handle"></div>
                        </div>
                    </div>
                    <div class="time-total">0:00</div>
                </div>
                
                <audio id="html5-audio" preload="auto">
                    Votre navigateur ne supporte pas la lecture audio.
                </audio>
                
                <div class="playlist" id="playlist">
                    <h4>🎵 Playlist</h4>
                    <div class="playlist-items" id="playlist-items">
                        <p class="empty-playlist">La playlist est vide</p>
                    </div>
                </div>
            </div>
        `;
        
        // Références aux éléments
        this.audio = this.container.querySelector('#html5-audio');
        this.playBtn = this.container.querySelector('#play-btn');
        this.prevBtn = this.container.querySelector('#prev-btn');
        this.nextBtn = this.container.querySelector('#next-btn');
        this.trackTitle = this.container.querySelector('.track-title');
        this.trackMeta = this.container.querySelector('.track-meta');
        this.timeCurrent = this.container.querySelector('.time-current');
        this.timeTotal = this.container.querySelector('.time-total');
        this.progressFill = this.container.querySelector('.progress-fill');
        this.progressHandle = this.container.querySelector('.progress-handle');
        this.progressTrack = this.container.querySelector('.progress-track');
        this.playlistItems = this.container.querySelector('#playlist-items');
    }
    
    attachEvents() {
        // Contrôles
        this.playBtn.addEventListener('click', () => this.togglePlay());
        this.prevBtn.addEventListener('click', () => this.previousTrack());
        this.nextBtn.addEventListener('click', () => this.nextTrack());
        
        // Événements audio
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.trackEnded());
        this.audio.addEventListener('canplay', () => this.enableControls());
        this.audio.addEventListener('error', (e) => this.handleError(e));
        
        // Barre de progression
        this.progressTrack.addEventListener('click', (e) => this.seekTo(e));
        
        // Support mobile
        this.progressTrack.addEventListener('touchstart', (e) => this.handleTouchStart(e), {passive: true});
        this.progressTrack.addEventListener('touchmove', (e) => this.handleTouchMove(e), {passive: false});
        this.progressTrack.addEventListener('touchend', () => this.handleTouchEnd());
    }
    
    addTrack(audioUrl, metadata = {}) {
        const track = {
            id: Date.now() + Math.random(),
            url: audioUrl,
            title: this.extractTitle(metadata),
            keywords: metadata.keywords || [],
            duration: metadata.duration_seconds || 0,
            timestamp: new Date().toLocaleTimeString(),
            metadata: metadata
        };
        
        this.playlist.push(track);
        this.updatePlaylistUI();
        
        // Si c'est le premier track, le charger
        if (this.playlist.length === 1) {
            this.loadTrack(0);
        }
        
        console.log(`🎵 Track ajouté: ${track.title}`);
        return track.id;
    }
    
    extractTitle(metadata) {
        if (metadata.phrases && metadata.phrases.length > 0) {
            return metadata.phrases[0].text.substring(0, 50) + '...';
        }
        if (metadata.title) return metadata.title;
        return `Phrase générée ${new Date().toLocaleTimeString()}`;
    }
    
    loadTrack(index) {
        if (index < 0 || index >= this.playlist.length) return;
        
        const track = this.playlist[index];
        this.currentTrackIndex = index;
        
        // Arrêter la lecture actuelle
        this.audio.pause();
        
        // Charger le nouveau track
        this.audio.src = track.url;
        this.audio.load();
        
        // Mettre à jour l'interface
        this.updateTrackInfo(track);
        this.updatePlaylistUI();
        
        console.log(`🎧 Track chargé: ${track.title}`);
    }
    
    updateTrackInfo(track) {
        this.trackTitle.textContent = track.title;
        
        let metaInfo = [];
        if (track.keywords.length > 0) {
            metaInfo.push(`🎯 ${track.keywords.slice(0, 3).join(', ')}`);
        }
        metaInfo.push(`⏰ ${track.timestamp}`);
        
        this.trackMeta.textContent = metaInfo.join(' • ');
    }
    
    updatePlaylistUI() {
        if (this.playlist.length === 0) {
            this.playlistItems.innerHTML = '<p class="empty-playlist">La playlist est vide</p>';
            return;
        }
        
        this.playlistItems.innerHTML = this.playlist.map((track, index) => `
            <div class="playlist-item ${index === this.currentTrackIndex ? 'active' : ''}" 
                 data-index="${index}">
                <div class="item-number">${index + 1}.</div>
                <div class="item-info">
                    <div class="item-title">${track.title}</div>
                    <div class="item-meta">
                        ${track.keywords.length > 0 ? `🎯 ${track.keywords.slice(0, 2).join(', ')}` : ''}
                        <span class="item-duration">⏱️ ${this.formatDuration(track.duration)}</span>
                    </div>
                </div>
                <button class="item-play-btn" data-index="${index}">
                    ${index === this.currentTrackIndex && this.isPlaying ? '⏸' : '▶'}
                </button>
            </div>
        `).join('');
        
        // Attacher événements playlist
        this.playlistItems.querySelectorAll('.playlist-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const index = parseInt(e.currentTarget.dataset.index);
                this.loadTrack(index);
            });
        });
        
        this.playlistItems.querySelectorAll('.item-play-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = parseInt(e.target.dataset.index);
                if (index === this.currentTrackIndex) {
                    this.togglePlay();
                } else {
                    this.loadTrack(index);
                    setTimeout(() => this.play(), 100);
                }
            });
        });
    }
    
    togglePlay() {
        if (!this.audio.src) return;
        
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    play() {
        this.audio.play().then(() => {
            this.isPlaying = true;
            this.playBtn.textContent = '⏸';
            this.updatePlaylistUI();
            console.log('▶ Lecture démarrée');
        }).catch(error => {
            console.error('❌ Erreur lecture:', error);
        });
    }
    
    pause() {
        this.audio.pause();
        this.isPlaying = false;
        this.playBtn.textContent = '▶';
        this.updatePlaylistUI();
        console.log('⏸ Lecture mise en pause');
    }
    
    previousTrack() {
        if (this.currentTrackIndex > 0) {
            this.loadTrack(this.currentTrackIndex - 1);
        }
    }
    
    nextTrack() {
        if (this.currentTrackIndex < this.playlist.length - 1) {
            this.loadTrack(this.currentTrackIndex + 1);
        }
    }
    
    trackEnded() {
        this.isPlaying = false;
        this.playBtn.textContent = '▶';
        
        // Lecture automatique du suivant
        if (this.currentTrackIndex < this.playlist.length - 1) {
            setTimeout(() => {
                this.nextTrack();
                this.play();
            }, 500);
        }
        
        this.updatePlaylistUI();
    }
    
    updateDuration() {
        const duration = this.audio.duration;
        this.timeTotal.textContent = this.formatTime(duration);
        
        // Mettre à jour la durée dans la playlist
        if (this.currentTrackIndex >= 0) {
            this.playlist[this.currentTrackIndex].duration = duration;
        }
    }
    
    updateProgress() {
        if (!this.audio.duration) return;
        
        const progress = (this.audio.currentTime / this.audio.duration) * 100;
        this.progressFill.style.width = progress + '%';
        this.progressHandle.style.left = progress + '%';
        
        this.timeCurrent.textContent = this.formatTime(this.audio.currentTime);
    }
    
    seekTo(e) {
        if (!this.audio.duration) return;
        
        const rect = this.progressTrack.getBoundingClientRect();
        const percent = (e.clientX - rect.left) / rect.width;
        const seekTime = percent * this.audio.duration;
        
        this.audio.currentTime = seekTime;
    }
    
    handleTouchStart(e) {
        this.isDragging = true;
    }
    
    handleTouchMove(e) {
        if (!this.isDragging || !this.audio.duration) return;
        
        e.preventDefault();
        const touch = e.touches[0];
        const rect = this.progressTrack.getBoundingClientRect();
        const percent = Math.max(0, Math.min(1, (touch.clientX - rect.left) / rect.width));
        
        this.progressFill.style.width = (percent * 100) + '%';
        this.progressHandle.style.left = (percent * 100) + '%';
        
        const seekTime = percent * this.audio.duration;
        this.timeCurrent.textContent = this.formatTime(seekTime);
    }
    
    handleTouchEnd() {
        if (this.isDragging && this.audio.duration) {
            const percent = parseFloat(this.progressHandle.style.left) / 100;
            const seekTime = percent * this.audio.duration;
            this.audio.currentTime = seekTime;
        }
        this.isDragging = false;
    }
    
    enableControls() {
        this.playBtn.disabled = false;
        this.prevBtn.disabled = this.currentTrackIndex <= 0;
        this.nextBtn.disabled = this.currentTrackIndex >= this.playlist.length - 1;
    }
    
    handleError(e) {
        console.error('❌ Erreur audio:', e);
        this.trackTitle.textContent = 'Erreur de chargement';
        this.trackMeta.textContent = 'Impossible de lire ce fichier audio';
    }
    
    formatTime(seconds) {
        if (!seconds || isNaN(seconds)) return '0:00';
        
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    formatDuration(seconds) {
        if (!seconds) return 'N/A';
        return this.formatTime(seconds);
    }
    
    // API publique
    clearPlaylist() {
        this.playlist = [];
        this.currentTrackIndex = -1;
        this.audio.src = '';
        this.isPlaying = false;
        this.playBtn.textContent = '▶';
        this.trackTitle.textContent = 'Aucun audio chargé';
        this.trackMeta.textContent = '';
        this.updatePlaylistUI();
        this.enableControls();
    }
    
    getPlaylist() {
        return [...this.playlist];
    }
    
    getCurrentTrack() {
        return this.currentTrackIndex >= 0 ? this.playlist[this.currentTrackIndex] : null;
    }
}

// Export pour utilisation globale
window.HTML5AudioPlayer = HTML5AudioPlayer;