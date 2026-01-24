// Script principal pour orchestrer tous les composants audio
class AudioInterface {
    constructor() {
        this.player = null;
        this.visualizer = null;
        this.spiderSemantic = null;
        this.currentAudioElement = null;
        this.visualizerConnected = false;
        this.addedTracks = new Set(); // Tracking pour éviter les doublons
        
        // L'initialisation sera appelée manuellement
    }
    
    async init() {
        await this.createInterface();
        this.initializeComponents();
        this.attachEvents();
        
        console.log('🎼 Interface audio modulaire initialisée');
    }
    
    async createInterface() {
        const container = document.getElementById('audio-interface-container') || 
                         document.querySelector('.audio-interface');
        
        if (!container) {
            console.error('❌ Container audio-interface non trouvé');
            return;
        }
        
        container.innerHTML = `
            <div class="new-audio-interface">
                <div class="player-section">
                    <div id="html5-player-container"></div>
                </div>
                
                <div class="visualization-section">
                    <div id="audio-visualizer-container"></div>
                </div>
                
                <div class="analysis-section">
                    <div id="spider-semantic-container"></div>
                </div>
            </div>
        `;
    }
    
    initializeComponents() {
        try {
            // Vérifier que les classes sont disponibles
            if (typeof HTML5AudioPlayer === 'undefined') {
                throw new Error('HTML5AudioPlayer non défini');
            }
            if (typeof SimpleAudioVisualizer === 'undefined') {
                throw new Error('SimpleAudioVisualizer non défini');  
            }
            if (typeof SpiderSemantic === 'undefined') {
                console.warn('⚠️ SpiderSemantic non disponible, composant désactivé');
                this.spiderSemantic = null;
            }
            
            // Initialiser le player HTML5
            this.player = new HTML5AudioPlayer('html5-player-container');
            
            // Initialiser le visualiseur
            this.visualizer = new SimpleAudioVisualizer('audio-visualizer-container', {
                width: 400,
                height: 200
            });
            
            // Initialiser le spider semantic si disponible
            if (typeof SpiderSemantic !== 'undefined') {
                this.spiderSemantic = new SpiderSemantic('spider-semantic-container', {
                    size: 300
                });
            } else {
                this.spiderSemantic = null;
            }
            
            console.log('✅ Tous les composants initialisés');
        } catch (error) {
            console.error('❌ Erreur initialisation composants:', error);
        }
    }
    
    attachEvents() {
        // Écouter les changements d'audio dans le player
        if (this.player && this.player.audio) {
            this.player.audio.addEventListener('loadeddata', () => {
                this.connectVisualizerToAudio();
            });
            
            this.player.audio.addEventListener('play', () => {
                if (this.visualizer) {
                    this.visualizer.startVisualization();
                }
            });
            
            this.player.audio.addEventListener('pause', () => {
                if (this.visualizer) {
                    this.visualizer.stopVisualization();
                }
            });
        }
    }
    
    connectVisualizerToAudio() {
        if (this.visualizer && this.player && this.player.audio) {
            this.visualizer.setAudioElement(this.player.audio);
            console.log('🔗 Visualiseur connecté au player');
        }
    }
    
    // API publique pour ajouter un nouveau track avec métadonnées complètes
    addTrack(audioUrl, metadata = {}) {
        if (!this.player) {
            console.error('❌ Player non initialisé');
            return;
        }
        
        // Vérifier les doublons
        if (this.addedTracks.has(audioUrl)) {
            console.log('⚠️ Track déjà ajouté, ignoré:', audioUrl.substring(audioUrl.lastIndexOf('/') + 1));
            return null;
        }
        
        // Marquer comme ajouté
        this.addedTracks.add(audioUrl);
        
        // Ajouter au player
        const trackId = this.player.addTrack(audioUrl, metadata);
        
        // Mettre à jour l'analyse sémantique
        if (this.spiderSemantic && metadata) {
            this.spiderSemantic.updateData(metadata, true);
        }
        
        // Connecter le visualiseur seulement si ce n'est pas déjà fait
        if (!this.visualizerConnected) {
            setTimeout(() => {
                this.connectVisualizerToAudio();
                this.visualizerConnected = true;
            }, 500);
        }
        
        console.log(`🎵 Track ajouté avec ID: ${trackId}`);
        return trackId;
    }
    
    // Méthodes de contrôle
    play() {
        if (this.player) {
            this.player.play();
        }
    }
    
    pause() {
        if (this.player) {
            this.player.pause();
        }
    }
    
    nextTrack() {
        if (this.player) {
            this.player.nextTrack();
        }
    }
    
    previousTrack() {
        if (this.player) {
            this.player.previousTrack();
        }
    }
    
    // Méthodes d'analyse
    updateSemanticAnalysis(data) {
        if (this.spiderSemantic) {
            this.spiderSemantic.updateData(data, true);
        }
    }
    
    setVisualizationMode(mode) {
        if (this.visualizer) {
            this.visualizer.setVisualizationMode(mode);
        }
    }
    
    // Méthodes utilitaires
    clearAll() {
        if (this.player) {
            this.player.clearPlaylist();
        }
        
        if (this.spiderSemantic) {
            this.spiderSemantic.clear();
        }
        
        if (this.visualizer) {
            this.visualizer.stopVisualization();
        }
    }
    
    getState() {
        return {
            playlist: this.player ? this.player.getPlaylist() : [],
            currentTrack: this.player ? this.player.getCurrentTrack() : null,
            semanticAnalysis: this.spiderSemantic ? this.spiderSemantic.export() : null,
            visualizationData: this.visualizer ? {
                frequency: this.visualizer.getFrequencyData(),
                waveform: this.visualizer.getWaveformData()
            } : null
        };
    }
    
    // Compatibilité avec l'ancienne interface
    loadAudioFile(url, metadata = {}) {
        return this.addTrack(url, metadata);
    }
    
    destroy() {
        if (this.visualizer) {
            this.visualizer.destroy();
        }
        
        if (this.player) {
            this.player.clearPlaylist();
        }
        
        console.log('🗑️ Interface audio détruite');
    }
}

// Fonction d'initialisation globale
async function initializeNewAudioInterface() {
    if (window.audioInterface) {
        window.audioInterface.destroy();
    }
    
    window.audioInterface = new AudioInterface();
    
    // Attendre que l'initialisation soit terminée
    await window.audioInterface.init();
    
    return window.audioInterface;
}

// Fonctions de compatibilité pour l'ancienne interface
function addTrackToPlaylist(audioUrl, metadata) {
    if (window.audioInterface) {
        return window.audioInterface.addTrack(audioUrl, metadata);
    } else {
        console.warn('⚠️ Interface audio non initialisée');
        return null;
    }
}

function loadAudioFile(audioUrl, metadata = {}) {
    return addTrackToPlaylist(audioUrl, metadata);
}

// Export pour utilisation globale
window.AudioInterface = AudioInterface;
window.initializeNewAudioInterface = initializeNewAudioInterface;
window.addTrackToPlaylist = addTrackToPlaylist;
window.loadAudioFile = loadAudioFile;

console.log('🎼 Script principal audio modulaire chargé');