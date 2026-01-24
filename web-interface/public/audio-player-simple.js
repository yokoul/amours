// Player audio HTML5 simple et responsive
class SimpleAudioPlayer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentTrack = null;
        this.playlist = [];
        this.currentIndex = -1;
        this.isPlaying = false;
        
        this.init();
    }
    
    init() {
        this.createPlayerHTML();
        this.setupEventListeners();
        console.log('🎵 SimpleAudioPlayer initialisé');
    }
    
    createPlayerHTML() {
        this.container.innerHTML = `
            <div class="audio-player-container">
                <!-- Audio Element -->
                <audio id="audio-element" preload="metadata"></audio>
                
                <!-- Player Interface -->
                <div class="player-interface">
                    <div class="track-info">
                        <h3 id="track-title">Aucun audio sélectionné</h3>
                        <p id="track-keywords"></p>
                    </div>
                    
                    <div class="player-controls">
                        <button id="prev-btn" class="control-btn">⏮</button>
                        <button id="play-btn" class="control-btn play-btn">▶</button>
                        <button id="next-btn" class="control-btn">⏭</button>
                    </div>
                    
                    <div class="progress-container">
                        <span id="current-time">0:00</span>
                        <div class="progress-bar">
                            <div id="progress-fill"></div>
                            <div id="progress-handle"></div>
                        </div>
                        <span id="duration">0:00</span>
                    </div>
                </div>
                
                <!-- Playlist -->
                <div class="playlist-container">
                    <h4>🎵 Playlist (<span id="playlist-count">0</span>)</h4>
                    <div id="playlist-tracks" class="playlist-tracks"></div>
                </div>
            </div>
        `;
        
        // Récupérer les références DOM
        this.audioElement = document.getElementById('audio-element');
        this.playBtn = document.getElementById('play-btn');
        this.prevBtn = document.getElementById('prev-btn');
        this.nextBtn = document.getElementById('next-btn');
        this.trackTitle = document.getElementById('track-title');
        this.trackKeywords = document.getElementById('track-keywords');
        this.currentTimeEl = document.getElementById('current-time');
        this.durationEl = document.getElementById('duration');
        this.progressFill = document.getElementById('progress-fill');
        this.progressHandle = document.getElementById('progress-handle');
        this.progressBar = document.querySelector('.progress-bar');
        this.playlistTracks = document.getElementById('playlist-tracks');
        this.playlistCount = document.getElementById('playlist-count');
    }
    
    setupEventListeners() {
        // Contrôles audio
        this.playBtn.addEventListener('click', () => this.togglePlay());
        this.prevBtn.addEventListener('click', () => this.prevTrack());
        this.nextBtn.addEventListener('click', () => this.nextTrack());
        
        // Événements audio
        this.audioElement.addEventListener('loadedmetadata', () => this.onMetadataLoaded());
        this.audioElement.addEventListener('timeupdate', () => this.onTimeUpdate());
        this.audioElement.addEventListener('ended', () => this.onTrackEnded());
        this.audioElement.addEventListener('play', () => this.onPlay());
        this.audioElement.addEventListener('pause', () => this.onPause());
        
        // Barre de progression
        this.progressBar.addEventListener('click', (e) => this.onProgressClick(e));
        
        // Responsive
        window.addEventListener('resize', () => this.onResize());
    }
    
    addTrack(audioUrl, metadata = {}) {
        const track = {
            id: Date.now(),
            audioUrl: audioUrl,
            title: metadata.phrases ? metadata.phrases[0].text.substring(0, 60) + '...' : 'Phrase générée',
            keywords: metadata.keywords || [],
            duration: metadata.duration_seconds || 0,
            timestamp: new Date().toLocaleTimeString(),
            metadata: metadata
        };
        
        this.playlist.push(track);
        this.updatePlaylistUI();
        
        // Si c'est le premier track, le sélectionner
        if (this.playlist.length === 1) {
            this.selectTrack(0);
        }
        
        console.log('🎵 Track ajouté:', track.title);
        return track;
    }
    
    selectTrack(index) {
        if (index < 0 || index >= this.playlist.length) return;
        
        this.currentIndex = index;
        this.currentTrack = this.playlist[index];
        
        // Charger l'audio
        this.audioElement.src = this.currentTrack.audioUrl;
        
        // Mettre à jour l'interface
        this.updateTrackInfo();
        this.updatePlaylistUI();
        
        console.log('🎧 Track sélectionné:', this.currentTrack.title);
    }
    
    updateTrackInfo() {
        if (!this.currentTrack) return;
        
        this.trackTitle.textContent = this.currentTrack.title;
        this.trackKeywords.textContent = this.currentTrack.keywords.join(' • ');
    }
    
    updatePlaylistUI() {
        this.playlistCount.textContent = this.playlist.length;
        
        this.playlistTracks.innerHTML = '';
        
        this.playlist.forEach((track, index) => {
            const trackEl = document.createElement('div');
            trackEl.className = `playlist-track ${index === this.currentIndex ? 'active' : ''}`;
            
            trackEl.innerHTML = `
                <div class="track-number">${index + 1}</div>
                <div class="track-details">
                    <div class="track-title">${track.title}</div>
                    <div class="track-meta">
                        <span class="track-time">⏱️ ${this.formatTime(track.duration)}</span>
                        <span class="track-keywords">🏷️ ${track.keywords.slice(0, 2).join(' • ')}</span>
                    </div>
                </div>
            `;
            
            trackEl.addEventListener('click', () => this.selectTrack(index));
            this.playlistTracks.appendChild(trackEl);
        });
    }
    
    togglePlay() {
        if (!this.currentTrack) return;
        
        if (this.isPlaying) {
            this.audioElement.pause();
        } else {
            this.audioElement.play();
        }
    }
    
    prevTrack() {
        if (this.playlist.length === 0) return;
        let prevIndex = this.currentIndex === 0 ? this.playlist.length - 1 : this.currentIndex - 1;
        this.selectTrack(prevIndex);
    }
    
    nextTrack() {
        if (this.playlist.length === 0) return;
        let nextIndex = (this.currentIndex + 1) % this.playlist.length;
        this.selectTrack(nextIndex);
    }
    
    // Événements audio
    onMetadataLoaded() {
        this.durationEl.textContent = this.formatTime(this.audioElement.duration);
    }
    
    onTimeUpdate() {
        const progress = (this.audioElement.currentTime / this.audioElement.duration) * 100;
        this.progressFill.style.width = `${progress}%`;
        this.progressHandle.style.left = `${progress}%`;
        this.currentTimeEl.textContent = this.formatTime(this.audioElement.currentTime);
    }
    
    onTrackEnded() {
        this.nextTrack();
    }
    
    onPlay() {
        this.isPlaying = true;
        this.playBtn.textContent = '⏸';
        this.playBtn.classList.add('playing');
    }
    
    onPause() {
        this.isPlaying = false;
        this.playBtn.textContent = '▶';
        this.playBtn.classList.remove('playing');
    }
    
    onProgressClick(e) {
        if (!this.audioElement.duration) return;
        
        const rect = this.progressBar.getBoundingClientRect();
        const progress = (e.clientX - rect.left) / rect.width;
        this.audioElement.currentTime = progress * this.audioElement.duration;
    }
    
    onResize() {
        // Gestion responsive si nécessaire
        console.log('📱 Resize détecté');
    }
    
    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    // API publique
    getPlaylist() {
        return this.playlist;
    }
    
    getCurrentTrack() {
        return this.currentTrack;
    }
    
    clearPlaylist() {
        this.playlist = [];
        this.currentIndex = -1;
        this.currentTrack = null;
        this.updatePlaylistUI();
        this.audioElement.src = '';
        this.trackTitle.textContent = 'Aucun audio sélectionné';
        this.trackKeywords.textContent = '';
    }
}

// Export pour utilisation
window.SimpleAudioPlayer = SimpleAudioPlayer;