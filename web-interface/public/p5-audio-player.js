// Player audio interactif p5.js avec playlist et visualisations sémantiques
let audioPlayer;
let canvas;
let isLoaded = false;
let isPlaying = false;
let currentAudioUrl = null;
let duration = 0;
let currentTime = 0;
let amplitude;
let fft;
let mousePressed = false;
let particleSystem = [];

// Playlist et historique
let playlist = [];
let currentTrackIndex = -1;
let showPlaylist = false;

// Variables visuelles
let bgHue = 280; // Violet/rose initial
let visualMode = 'spider'; // 'waves', 'particles', 'spectrum', 'spider'

// Spider chart données
let spiderData = null;

class AudioVisualizer {
    constructor() {
        this.setup();
    }

    setup() {
        // DIMENSIONS PLEINE LARGEUR RESPONSIVE
        const container = document.getElementById('p5-audio-container');
        let canvasWidth = window.innerWidth - 40; // Presque pleine largeur avec marges
        let canvasHeight = window.innerHeight * 0.8; // 80% de la hauteur viewport
        
        // Minima et maxima sensés
        canvasWidth = Math.max(320, Math.min(canvasWidth, 2000));
        canvasHeight = Math.max(400, Math.min(canvasHeight, 1200));
        
        console.log(`🎨 Canvas pleine largeur: ${canvasWidth}x${canvasHeight}`);
        
        canvas = createCanvas(canvasWidth, canvasHeight);
        canvas.parent('p5-audio-container');
        
        // CORRECTION TEXTE NET selon p5.js docs
        pixelDensity(displayDensity()); // Utiliser la densité native
        
        // Configuration typographie optimale p5.js
        textAlign(LEFT, BASELINE);
        textFont('system-ui, -apple-system, Arial, sans-serif'); // Police système optimale
        
        colorMode(HSB, 360, 100, 100, 100);
        
        // Initialiser l'analyse audio
        amplitude = new p5.Amplitude();
        fft = new p5.FFT(0.8, 1024);
        
        // Système de particules adaptatif
        const numParticles = window.innerWidth <= 768 ? 20 : 40;
        for (let i = 0; i < numParticles; i++) {
            particleSystem.push(new AudioParticle());
        }
        
        console.log('✅ Canvas p5.js créé et configuré avec support mobile');
    }

    addToPlaylist(audioUrl, metadata) {
        const track = {
            id: Date.now(),
            audioUrl: audioUrl,
            title: metadata.phrases ? metadata.phrases[0].text.substring(0, 50) + '...' : 'Phrase générée',
            keywords: metadata.keywords || [],
            duration: metadata.duration_seconds || 0,
            timestamp: metadata.timestamp || new Date().toLocaleTimeString(),
            spiderData: this.generateSpiderData(metadata)
        };
        
        playlist.push(track);
        
        // Si c'est le premier track ou qu'aucun n'est en cours, le jouer
        if (playlist.length === 1 || currentTrackIndex === -1) {
            this.playTrack(playlist.length - 1);
        }
        
        console.log('🎵 Ajouté à la playlist:', track.title);
    }

    generateSpiderData(metadata) {
        // Générer des données spider basées sur les mots-clés et l'analyse sémantique
        const spiderCategories = [
            'Passion', 'Tendresse', 'Désir', 'Romance', 
            'Mélancolie', 'Espoir', 'Sensualité', 'Poésie'
        ];
        
        const data = {};
        
        // Scores basés sur les mots-clés présents
        spiderCategories.forEach(category => {
            let score = Math.random() * 0.3 + 0.1; // Score de base
            
            // Augmenter selon les mots-clés
            if (metadata.keywords) {
                metadata.keywords.forEach(keyword => {
                    if (this.isRelatedToCategory(keyword.toLowerCase(), category.toLowerCase())) {
                        score += Math.random() * 0.6 + 0.4;
                    }
                });
            }
            
            data[category] = Math.min(score, 1.0);
        });
        
        return data;
    }

    isRelatedToCategory(keyword, category) {
        const relations = {
            'passion': ['amour', 'passion', 'feu', 'ardent', 'brûler'],
            'tendresse': ['tendresse', 'doux', 'caresse', 'câlin', 'bienveillance'],
            'désir': ['désir', 'envie', 'attraction', 'séduction', 'charme'],
            'romance': ['romance', 'romantique', 'rêve', 'conte', 'prince'],
            'mélancolie': ['mélancolie', 'tristesse', 'nostalgie', 'absence', 'manque'],
            'espoir': ['espoir', 'futur', 'demain', 'possible', 'ensemble'],
            'sensualité': ['sensuel', 'peau', 'toucher', 'corps', 'sensation'],
            'poésie': ['poésie', 'vers', 'rime', 'beauté', 'art']
        };
        
        return relations[category] && relations[category].includes(keyword);
    }

    playTrack(index) {
        if (index < 0 || index >= playlist.length) return;
        
        currentTrackIndex = index;
        const track = playlist[index];
        spiderData = track.spiderData;
        
        this.loadAudio(track.audioUrl, track);
        console.log('🎧 Lecture:', track.title);
    }

    nextTrack() {
        if (playlist.length === 0) return;
        let nextIndex = (currentTrackIndex + 1) % playlist.length;
        this.playTrack(nextIndex);
    }

    prevTrack() {
        if (playlist.length === 0) return;
        let prevIndex = currentTrackIndex === 0 ? playlist.length - 1 : currentTrackIndex - 1;
        this.playTrack(prevIndex);
    }

    loadAudio(audioUrl, metadata = {}) {
        if (currentAudioUrl === audioUrl) return;
        
        if (audioPlayer) {
            audioPlayer.stop();
            audioPlayer = null;
        }
        
        currentAudioUrl = audioUrl;
        console.log('🎵 Chargement audio p5.js:', audioUrl);
        
        // IMPORTANT: Activer l'AudioContext sur mobile au premier clic
        if (getAudioContext && getAudioContext().state === 'suspended') {
            console.log('📱 Activation AudioContext pour mobile...');
            getAudioContext().resume().then(() => {
                console.log('✅ AudioContext activé');
                this.actuallyLoadSound(audioUrl, metadata);
            });
        } else {
            this.actuallyLoadSound(audioUrl, metadata);
        }
    }
    
    actuallyLoadSound(audioUrl, metadata = {}) {
        // Utiliser l'API p5.js correcte pour charger l'audio
        audioPlayer = loadSound(audioUrl, 
            // Callback de succès
            () => {
                console.log('✅ Audio p5.js chargé avec succès');
                isLoaded = true;
                duration = audioPlayer.duration();
                
                // Connecter à l'analyseur après chargement
                amplitude.setInput(audioPlayer);
                fft.setInput(audioPlayer);
            },
            // Callback d'erreur
            (error) => {
                console.error('❌ Erreur chargement audio p5.js:', error);
                isLoaded = false;
            }
        );
        
        // Pas besoin de onended avec p5.js - on utilisera isPlaying() dans draw()
        isLoaded = false;
    }

    draw() {
        background(0, 0, 5, 95); // Fond très sombre
        
        // Toujours afficher quelque chose, même sans audio
        if (!audioPlayer && playlist.length === 0) {
            this.drawPlaceholder();
            return;
        }
        
        // Mettre à jour le statut de lecture
        this.updatePlaybackStatus();
        
        // Layout : playlist à gauche, visualisation au centre, spider à droite
        try {
            this.drawLayout();
        } catch (error) {
            console.error('❌ Erreur dans drawLayout:', error);
            this.drawPlaceholder(); // Fallback
        }
    }

    drawLayout() {
        let level = amplitude.getLevel();
        bgHue = (bgHue + level * 30) % 360;
        
        // LAYOUT UNIFIÉ EN 3 ZONES VERTICALES
        
        // Zone 1: Contrôles (20%)
        this.drawControlsSection(height * 0.2);
        
        // Zone 2: Visualisation principale (60%) 
        this.drawVisualizationSection(height * 0.2, height * 0.6, level);
        
        // Zone 3: Playlist + Spider (20%)
        if (playlist.length > 0) {
            this.drawPlaylistSection(height * 0.8, height * 0.2);
        }
    }
    
    // === MÉTHODES LAYOUT UNIFIÉES ===
    
    drawControlsSection(sectionHeight) {
        // Section contrôles: 0 à sectionHeight
        fill(0, 0, 15, 90);
        stroke(bgHue, 50, 70);
        strokeWeight(1);
        rect(0, 0, width, sectionHeight);
        
        // Info du track actuel
        if (currentTrackIndex >= 0 && playlist[currentTrackIndex]) {
            let track = playlist[currentTrackIndex];
            fill(bgHue, 80, 100);
            textAlign(LEFT, TOP);
            textSize(16); // Taille nette selon docs p5.js
            text(`🎵 ${track.title.substring(0, 45)}`, 15, 15);
            
            fill(0, 0, 70);
            textSize(12);
            text(`${track.keywords.slice(0, 4).join(' • ')}`, 15, 40);
        }
        
        // Boutons centrés
        let buttonY = sectionHeight / 2 + 15;
        let centerX = width / 2;
        let spacing = Math.min(80, width / 10);
        let buttonSize = Math.min(45, width / 20);
        
        // Boutons avec style p5.js optimisé
        this.drawControlButton(centerX - spacing, buttonY, buttonSize, "⏮", "prev");
        this.drawControlButton(centerX, buttonY, buttonSize + 10, isPlaying ? "⏸" : "▶", "play");
        this.drawControlButton(centerX + spacing, buttonY, buttonSize, "⏭", "next");
        
        // Sélecteur de mode visuel
        this.drawVisualModeSelector(sectionHeight - 50);
    }
    
    drawControlButton(x, y, size, label, action) {
        let isHover = dist(mouseX, mouseY, x, y) < size/2 + 10;
        let isPlayingBtn = action === "play" && isPlaying;
        
        // Style selon l'état
        if (isPlayingBtn) {
            fill(bgHue, 50, 80);
            stroke(bgHue, 70, 100);
        } else if (isHover) {
            fill(bgHue, 30, 60);
            stroke(bgHue, 60, 90);
        } else {
            fill(0, 0, 40);
            stroke(bgHue, 40, 70);
        }
        
        strokeWeight(2);
        ellipse(x, y, size);
        
        // Label centré
        fill(255);
        textAlign(CENTER, CENTER);
        textSize(size * 0.4);
        text(label, x, y);
        
        // Stocker zone tactile
        if (!this.controlZones) this.controlZones = {};
        this.controlZones[action] = { x: x, y: y, size: size + 20 };
    }
    
    drawVisualModeSelector(yPos) {
        // Sélecteur de mode visuel
        let modes = ['spectrum', 'particles', 'waves', 'spider'];
        let modeWidth = (width - 40) / modes.length;
        
        fill(bgHue, 60, 90);
        textAlign(LEFT, CENTER);
        textSize(10);
        text("Mode visuel:", 15, yPos - 10);
        
        for (let i = 0; i < modes.length; i++) {
            let mode = modes[i];
            let x = 15 + i * modeWidth;
            let isActive = visualMode === mode;
            
            if (isActive) {
                fill(bgHue, 60, 90);
                stroke(bgHue, 80, 100);
            } else {
                fill(0, 0, 30);
                stroke(0, 0, 50);
            }
            
            strokeWeight(1);
            rect(x, yPos, modeWidth - 5, 20, 5);
            
            fill(isActive ? 255 : [0, 0, 70]);
            textAlign(CENTER, CENTER);
            textSize(9);
            text(mode.toUpperCase(), x + modeWidth/2 - 2.5, yPos + 10);
            
            // Zone tactile
            if (!this.visualModeZones) this.visualModeZones = {};
            this.visualModeZones[mode] = { x: x, y: yPos, width: modeWidth - 5, height: 20 };
        }
    }
    
    drawVisualizationSection(startY, sectionHeight, level) {
        // Section visualisation: startY à startY + sectionHeight
        push();
        translate(0, startY);
        
        // Fond de la section
        fill(0, 0, 8, 70);
        stroke(bgHue, 20, 40);
        strokeWeight(1);
        rect(0, 0, width, sectionHeight);
        
        // Titre de la visualisation
        fill(bgHue, 70, 90);
        textAlign(CENTER, TOP);
        textSize(14);
        text(`🎵 ${visualMode.toUpperCase()} - ANALYSE TEMPS RÉEL`, width/2, 10);
        
        // Dessiner selon le mode sélectionné
        switch(visualMode) {
            case 'spectrum':
                this.drawSpectrumVisualization(30, sectionHeight - 60, level);
                break;
            case 'particles':
                this.drawParticleVisualization(30, sectionHeight - 60, level);
                break;
            case 'waves':
                this.drawWaveVisualization(30, sectionHeight - 60, level);
                break;
            case 'spider':
                this.drawSpiderVisualization(30, sectionHeight - 60, level);
                break;
        }
        
        pop();
    }
    
    drawPlaylistSection(startY, sectionHeight) {
        // Section playlist: startY à startY + sectionHeight
        push();
        translate(0, startY);
        
        // Fond playlist
        fill(0, 0, 12, 85);
        stroke(bgHue, 30, 50);
        strokeWeight(1);
        rect(0, 0, width, sectionHeight);
        
        // Header playlist
        fill(bgHue, 60, 90);
        textAlign(LEFT, TOP);
        textSize(12);
        text(`🎵 PLAYLIST (${playlist.length} tracks)`, 15, 10);
        
        // Tracks compacts horizontaux
        this.drawCompactPlaylist(30, sectionHeight - 40);
        
        pop();
    }
    
    drawCompactPlaylist(startY, availableHeight) {
        let trackWidth = Math.min(180, (width - 30) / Math.max(1, Math.min(playlist.length, 4)));
        let trackHeight = availableHeight - 10;
        
        for (let i = 0; i < Math.min(playlist.length, Math.floor(width / trackWidth)); i++) {
            let track = playlist[i];
            let x = 15 + i * (trackWidth + 10);
            
            // Style selon l'état
            if (i === currentTrackIndex) {
                fill(bgHue, 40, 30, 90);
                stroke(bgHue, 70, 90);
                strokeWeight(2);
            } else {
                fill(0, 0, 25, 80);
                stroke(0, 0, 45);
                strokeWeight(1);
            }
            
            rect(x, startY, trackWidth, trackHeight, 5);
            
            // Contenu track
            fill(i === currentTrackIndex ? [bgHue, 90, 100] : [0, 0, 90]);
            textAlign(LEFT, TOP);
            textSize(10);
            text(`${i + 1}. ${track.title.substring(0, 22)}`, x + 8, startY + 8);
            
            fill(0, 0, 70);
            textSize(8);
            text(`⏱️ ${this.formatTime(track.duration)}`, x + 8, startY + trackHeight - 15);
            
            // Zone tactile playlist (ajuster pour la position globale)
            if (!this.playlistZones) this.playlistZones = [];
            this.playlistZones[i] = { 
                x: x, 
                y: height * 0.8 + startY, // Position absolue pour le clic
                width: trackWidth, 
                height: trackHeight, 
                index: i 
            };
        }
    }
    
    drawCompactControlsTop() {
        // Zone contrôles: 0 à 20% de la hauteur
        let controlHeight = height * 0.2;
        
        // Fond contrôles
        fill(0, 0, 15, 90);
        stroke(bgHue, 50, 70);
        strokeWeight(1);
        rect(0, 0, width, controlHeight);
        
        // Info du track actuel
        if (currentTrackIndex >= 0 && playlist[currentTrackIndex]) {
            let track = playlist[currentTrackIndex];
            fill(bgHue, 80, 100);
            textAlign(LEFT, TOP);
            textSize(Math.floor(Math.max(10, width / 40))); // Taille ENTIÈRE
            text(`🎵 ${track.title.substring(0, 35)}`, 10, 10);
            
            fill(0, 0, 70);
            textSize(Math.floor(Math.max(8, width / 50))); // Taille ENTIÈRE
            text(`${track.keywords.slice(0, 3).join(' • ')}`, 10, 30);
        }
        
        // Boutons centrés
        let buttonY = controlHeight / 2 + 10;
        let centerX = width / 2;
        let spacing = Math.min(60, width / 8);
        let buttonSize = Math.min(35, width / 15);
        
        // Style boutons
        let normalColor = [0, 0, 40];
        let hoverColor = [bgHue, 30, 60];
        
        // Bouton PRÉCÉDENT
        let prevX = centerX - spacing;
        let isPrevHover = dist(mouseX, mouseY, prevX, buttonY) < buttonSize;
        
        fill(...(isPrevHover ? hoverColor : normalColor));
        stroke(bgHue, 40, 70);
        strokeWeight(2);
        ellipse(prevX, buttonY, buttonSize);
        fill(255);
        textAlign(CENTER, CENTER);
        textSize(buttonSize * 0.4);
        text("⏮", prevX, buttonY);
        
        // Bouton PLAY/PAUSE
        let playSize = buttonSize + 8;
        let isPlayHover = dist(mouseX, mouseY, centerX, buttonY) < playSize;
        
        fill(...(isPlaying ? [bgHue, 50, 80] : (isPlayHover ? hoverColor : normalColor)));
        stroke(bgHue, 60, 90);
        strokeWeight(2);
        ellipse(centerX, buttonY, playSize);
        fill(255);
        textSize(playSize * 0.4);
        text(isPlaying ? "⏸" : "▶", centerX, buttonY);
        
        // Bouton SUIVANT
        let nextX = centerX + spacing;
        let isNextHover = dist(mouseX, mouseY, nextX, buttonY) < buttonSize;
        
        fill(...(isNextHover ? hoverColor : normalColor));
        stroke(bgHue, 40, 70);
        strokeWeight(2);
        ellipse(nextX, buttonY, buttonSize);
        fill(255);
        textSize(buttonSize * 0.4);
        text("⏭", nextX, buttonY);
        
        // Stocker les zones tactiles
        this.controlZones = {
            prev: { x: prevX, y: buttonY, size: buttonSize + 10 },
            play: { x: centerX, y: buttonY, size: playSize + 10 },
            next: { x: nextX, y: buttonY, size: buttonSize + 10 }
        };
    }
    
    drawMainSpectrum(level) {
        // Zone spectrum: 20% à 80% de la hauteur
        let spectrumY = height * 0.2;
        let spectrumHeight = height * 0.6;
        
        push();
        translate(width / 2, spectrumY + spectrumHeight / 2);
        
        // Fond spectrum
        fill(0, 0, 5, 60);
        stroke(bgHue, 20, 40);
        strokeWeight(1);
        rectMode(CENTER);
        rect(0, 0, width - 20, spectrumHeight - 20, 15);
        
        // SPECTRUM FREQUENCY
        let spectrum = fft.analyze();
        let spectrumWidth = width - 60;
        let barWidth = spectrumWidth / (spectrum.length / 4);
        
        // Dessiner les barres du spectrum
        for (let i = 0; i < spectrum.length / 4; i++) {
            let amplitude = spectrum[i];
            let barHeight = map(amplitude, 0, 255, 5, spectrumHeight - 60);
            
            // Couleurs basées sur la fréquence et l'amplitude
            let hue = map(i, 0, spectrum.length / 4, bgHue - 40, bgHue + 40);
            let saturation = map(amplitude, 0, 255, 20, 80);
            let brightness = map(amplitude, 0, 255, 30, 90);
            
            fill(hue, saturation, brightness, 80);
            noStroke();
            
            let x = map(i, 0, spectrum.length / 4, -spectrumWidth/2, spectrumWidth/2);
            rect(x, 0, barWidth - 1, -barHeight);
            
            // Effet de reflet
            fill(hue, saturation, brightness, 30);
            rect(x, 0, barWidth - 1, barHeight / 4);
        }
        
        // Titre
        fill(bgHue, 70, 90, 70);
        textAlign(CENTER, CENTER);
        textSize(Math.floor(Math.max(12, width / 30))); // Taille ENTIÈRE
        text("🎵 ANALYSE SPECTRALE EN TEMPS RÉEL", 0, -spectrumHeight/2 + 30);
        
        pop();
    }
    
    drawBottomPlaylist() {
        // Zone playlist: 80% à 100% de la hauteur
        let playlistY = height * 0.8;
        let playlistHeight = height * 0.2;
        
        // Fond playlist
        fill(0, 0, 10, 85);
        stroke(bgHue, 30, 50);
        strokeWeight(1);
        rect(0, playlistY, width, playlistHeight);
        
        // Header playlist
        fill(bgHue, 60, 90);
        textAlign(LEFT, TOP);
        textSize(Math.floor(Math.max(10, width / 40))); // Taille ENTIÈRE
        text(`🎵 PLAYLIST (${playlist.length})`, 10, playlistY + 5);
        
        // Tracks horizontaux compacts
        let trackWidth = Math.min(150, width / 4);
        let trackY = playlistY + 25;
        let trackHeight = playlistHeight - 30;
        
        for (let i = 0; i < Math.min(playlist.length, Math.floor(width / trackWidth)); i++) {
            let track = playlist[i];
            let trackX = 10 + i * (trackWidth + 10);
            
            // Background track
            if (i === currentTrackIndex) {
                fill(bgHue, 40, 30, 90);
                stroke(bgHue, 70, 90);
                strokeWeight(2);
            } else {
                fill(0, 0, 20, 80);
                stroke(0, 0, 40);
                strokeWeight(1);
            }
            
            rect(trackX, trackY, trackWidth, trackHeight, 5);
            
            // Contenu track
            fill(i === currentTrackIndex ? [bgHue, 90, 100] : [0, 0, 90]);
            textAlign(LEFT, TOP);
            textSize(Math.floor(Math.max(8, width / 60))); // Taille ENTIÈRE
            text(`${i + 1}. ${track.title.substring(0, 20)}`, trackX + 5, trackY + 5);
            
            fill(0, 0, 70);
            textSize(Math.floor(Math.max(7, width / 70))); // Taille ENTIÈRE
            text(`⏱️ ${this.formatTime(track.duration)}`, trackX + 5, trackY + trackHeight - 15);
        }
    }

    drawPlaylist() {
        // VRAIE playlist tactile style Winamp
        let playlistWidth = 300;
        let playlistHeight = height - 140;
        
        // Fond playlist avec scroll
        fill(0, 0, 15, 95);
        stroke(bgHue, 60, 80);
        strokeWeight(2);
        rect(10, 10, playlistWidth, playlistHeight);
        
        // Header playlist
        fill(bgHue, 70, 100);
        rect(10, 10, playlistWidth, 35);
        
        fill(0, 0, 100);
        textAlign(CENTER, CENTER);
        textSize(14);
        text(`🎵 PLAYLIST (${playlist.length})`, 10 + playlistWidth/2, 27);
        
        // Zone scrollable des tracks
        let trackHeight = 55;
        let visibleTracks = Math.floor((playlistHeight - 35) / trackHeight);
        let scrollOffset = 0; // TODO: implémenter le scroll tactile
        
        // Dessiner les tracks visibles
        for (let i = 0; i < Math.min(playlist.length, visibleTracks); i++) {
            let track = playlist[i];
            let trackY = 50 + i * trackHeight;
            
            // Zone tactile pour chaque track
            let isTrackHover = mouseX >= 15 && mouseX <= 305 && 
                              mouseY >= trackY && mouseY <= trackY + trackHeight - 5;
            
            // Background du track
            if (i === currentTrackIndex) {
                // Track en cours
                fill(bgHue, 40, 30, 90);
                stroke(bgHue, 70, 90);
                strokeWeight(2);
            } else if (isTrackHover) {
                // Track survolé/touché
                fill(bgHue, 20, 40, 70);
                stroke(bgHue, 50, 70);
                strokeWeight(1);
            } else {
                // Track normal
                fill(0, 0, 20, 80);
                stroke(0, 0, 40);
                strokeWeight(1);
            }
            
            rect(15, trackY, 285, trackHeight - 5, 5);
            
            // Numéro du track
            fill(i === currentTrackIndex ? bgHue : 0, 0, 100);
            textAlign(LEFT, TOP);
            textSize(16);
            text(`${i + 1}.`, 25, trackY + 8);
            
            // Titre (tronqué si nécessaire)
            let title = track.title;
            if (title.length > 35) title = title.substring(0, 32) + '...';
            
            fill(i === currentTrackIndex ? [bgHue, 90, 100] : [0, 0, 90]);
            textSize(12);
            text(title, 45, trackY + 8);
            
            // Métadonnées
            fill(0, 0, 70);
            textSize(10);
            text(`⏱️ ${this.formatTime(track.duration)} • ${track.timestamp}`, 45, trackY + 25);
            
            // Keywords avec couleurs
            let keywordText = track.keywords.slice(0, 3).join(' • ');
            fill(bgHue, 50, 80);
            text(`🏷️ ${keywordText}`, 45, trackY + 38);
            
            // Boutons mini play/delete pour chaque track
            this.drawTrackButtons(track, i, trackY);
            
            // Stockage zone tactile
            if (!this.playlistTouchZones) this.playlistTouchZones = [];
            this.playlistTouchZones[i] = {
                x: 15, y: trackY, width: 285, height: trackHeight - 5, index: i
            };
        }
        
        // Indicateur de scroll si nécessaire
        if (playlist.length > visibleTracks) {
            this.drawScrollIndicator(playlistWidth, playlistHeight);
        }
    }

    drawTrackButtons(track, index, trackY) {
        let buttonSize = 25;
        let buttonY = trackY + 15;
        
        // Bouton play mini
        let playButtonX = 260;
        let isPlayHover = dist(mouseX, mouseY, playButtonX, buttonY) < buttonSize/2;
        
        fill(isPlayHover ? [bgHue, 40, 70] : [0, 0, 40]);
        stroke(isPlayHover ? [bgHue, 60, 90] : [0, 0, 60]);
        ellipse(playButtonX, buttonY, buttonSize);
        
        fill(255);
        textAlign(CENTER, CENTER);
        textSize(12);
        text(index === currentTrackIndex && isPlaying ? "⏸" : "▶", playButtonX, buttonY);
        
        // Bouton delete mini  
        let deleteButtonX = 285;
        let isDeleteHover = dist(mouseX, mouseY, deleteButtonX, buttonY) < buttonSize/2;
        
        fill(isDeleteHover ? [0, 80, 60] : [0, 0, 40]);
        stroke(isDeleteHover ? [0, 100, 80] : [0, 0, 60]);
        ellipse(deleteButtonX, buttonY, buttonSize);
        
        fill(255);
        text("×", deleteButtonX, buttonY);
        
        // Stockage zones boutons
        if (!this.trackButtonZones) this.trackButtonZones = [];
        this.trackButtonZones[index] = {
            play: { x: playButtonX, y: buttonY, size: buttonSize },
            delete: { x: deleteButtonX, y: buttonY, size: buttonSize }
        };
    }
    
    drawCenterSpectrum(level) {
        // SPECTRUM EN GRAND AU CENTRE
        let centerY = height * 0.35 + 20;
        let centerHeight = height * 0.45;
        
        // Zone spectrum
        push();
        translate(width / 2, centerY + centerHeight / 2);
        
        // Fond spectrum
        fill(0, 0, 5, 60);
        stroke(bgHue, 20, 40);
        rectMode(CENTER);
        rect(0, 0, width - 40, centerHeight - 40, 15);
        
        // SPECTRUM FREQUENCY GRAND ET BEAU
        let spectrum = fft.analyze();
        let spectrumWidth = width - 80;
        let spectrumHeight = centerHeight - 80;
        
        // Dessiner le spectrum avec des barres
        let barWidth = spectrumWidth / spectrum.length * 4; // Plus de barres visibles
        
        for (let i = 0; i < spectrum.length / 4; i++) {
            let amplitude = spectrum[i];
            let barHeight = map(amplitude, 0, 255, 5, spectrumHeight);
            
            // Couleur basée sur la fréquence
            let hue = map(i, 0, spectrum.length / 4, bgHue - 60, bgHue + 60);
            let saturation = map(amplitude, 0, 255, 30, 90);
            let brightness = map(amplitude, 0, 255, 40, 100);
            
            fill(hue, saturation, brightness, 80);
            stroke(hue, saturation + 20, brightness + 20);
            strokeWeight(0.5);
            
            let x = map(i, 0, spectrum.length / 4, -spectrumWidth/2, spectrumWidth/2);
            rect(x, 0, barWidth - 1, -barHeight);
            
            // Reflet en bas
            fill(hue, saturation, brightness, 30);
            rect(x, 0, barWidth - 1, barHeight / 3);
        }
        
        // Texte informatif
        fill(bgHue, 70, 90, 70);
        textAlign(CENTER, CENTER);
        textSize(width < 500 ? 12 : 16);
        text("🎵 ANALYSE SPECTRALE", 0, -centerHeight/2 + 25);
        
        pop();
    }
    
    drawBottomSpider() {
        // SPIDER CHART EN BAS
        let spiderY = height * 0.82;
        let spiderHeight = height * 0.18 - 10;
        let spiderSize = Math.min(spiderHeight - 20, 100);
        
        push();
        translate(width / 2, spiderY + spiderHeight / 2);
        
        // Fond spider
        fill(0, 0, 8, 70);
        stroke(bgHue, 25, 45);
        rectMode(CENTER);
        rect(0, 0, width - 20, spiderHeight, 10);
        
        // Spider chart compact
        this.drawCompactSpider(spiderSize);
        
        pop();
    }
    
    drawCompactSpider(size) {
        const categories = Object.keys(spiderData);
        const numCategories = categories.length;
        const angleStep = TWO_PI / numCategories;
        
        // Grille spider
        stroke(bgHue, 20, 60, 40);
        strokeWeight(0.5);
        noFill();
        
        // Cercles concentriques
        for (let r = size/4; r <= size/2; r += size/4) {
            ellipse(0, 0, r * 2);
        }
        
        // Lignes radiales
        for (let i = 0; i < numCategories; i++) {
            let angle = i * angleStep - PI/2;
            let x = cos(angle) * size/2;
            let y = sin(angle) * size/2;
            line(0, 0, x, y);
        }
        
        // Données spider
        fill(bgHue, 60, 80, 60);
        stroke(bgHue, 80, 100);
        strokeWeight(2);
        
        beginShape();
        for (let i = 0; i < numCategories; i++) {
            let category = categories[i];
            let value = spiderData[category];
            let angle = i * angleStep - PI/2;
            let radius = value * size/2;
            
            let x = cos(angle) * radius;
            let y = sin(angle) * radius;
            
            if (i === 0) {
                vertex(x, y);
            } else {
                vertex(x, y);
            }
        }
        endShape(CLOSE);
        
        // Labels (seulement les 4 principaux sur petit écran)
        fill(0, 0, 90, 80);
        textAlign(CENTER, CENTER);
        textSize(8);
        
        for (let i = 0; i < Math.min(numCategories, 4); i++) {
            let category = categories[i];
            let angle = i * angleStep - PI/2;
            let x = cos(angle) * (size/2 + 15);
            let y = sin(angle) * (size/2 + 15);
            
            text(category.substring(0, 6), x, y);
        }
    }

    drawScrollIndicator(playlistWidth, playlistHeight) {
        // TODO: Indicateur de scroll vertical tactile
        let scrollBarWidth = 8;
        let scrollBarX = 10 + playlistWidth - scrollBarWidth - 5;
        
        fill(0, 0, 30);
        rect(scrollBarX, 45, scrollBarWidth, playlistHeight - 40);
        
        // Thumb du scroll (simplifié pour l'instant)
        fill(bgHue, 50, 70);
        rect(scrollBarX + 1, 50, scrollBarWidth - 2, 30, 3);
    }

    drawSpiderChart() {
        if (!spiderData) return;
        
        let centerX = showPlaylist ? width - 150 : width - 120;
        let centerY = 120;
        let radius = 80;
        
        // Fond du spider chart
        fill(0, 0, 10, 80);
        stroke(bgHue, 30, 70);
        ellipse(centerX, centerY, radius * 2.2);
        
        // Titre
        fill(bgHue, 70, 100);
        textAlign(CENTER, TOP);
        textSize(12);
        text("Analyse Sémantique", centerX, centerY - radius - 25);
        
        let categories = Object.keys(spiderData);
        let angleStep = TWO_PI / categories.length;
        
        // Dessiner les axes
        stroke(0, 0, 40);
        strokeWeight(1);
        for (let i = 0; i < categories.length; i++) {
            let angle = i * angleStep - PI/2;
            let x = centerX + cos(angle) * radius;
            let y = centerY + sin(angle) * radius;
            line(centerX, centerY, x, y);
            
            // Labels
            fill(0, 0, 70);
            textAlign(CENTER, CENTER);
            textSize(9);
            text(categories[i], 
                centerX + cos(angle) * (radius + 15),
                centerY + sin(angle) * (radius + 15)
            );
        }
        
        // Cercles concentriques
        noFill();
        stroke(0, 0, 25);
        for (let r = 20; r <= radius; r += 20) {
            ellipse(centerX, centerY, r * 2);
        }
        
        // Dessiner le polygone des données
        fill(bgHue, 60, 70, 60);
        stroke(bgHue, 80, 90);
        strokeWeight(2);
        beginShape();
        for (let i = 0; i < categories.length; i++) {
            let angle = i * angleStep - PI/2;
            let value = spiderData[categories[i]];
            let x = centerX + cos(angle) * (radius * value);
            let y = centerY + sin(angle) * (radius * value);
            vertex(x, y);
        }
        endShape(CLOSE);
        
        // Points de données
        fill(bgHue, 90, 100);
        noStroke();
        for (let i = 0; i < categories.length; i++) {
            let angle = i * angleStep - PI/2;
            let value = spiderData[categories[i]];
            let x = centerX + cos(angle) * (radius * value);
            let y = centerY + sin(angle) * (radius * value);
            ellipse(x, y, 6);
        }
    }

    drawMainVisualization(level) {
        let spectrum = fft.analyze();
        
        switch (visualMode) {
            case 'waves':
                this.drawWaves(spectrum, level);
                break;
            case 'particles':
                this.drawParticles(level);
                break;
            case 'spectrum':
                this.drawSpectrum(spectrum, level);
                break;
            case 'spider':
                // Dans ce mode, la visualisation principale est plus petite
                scale(0.7);
                this.drawWaves(spectrum, level);
                break;
        }
    }

    drawWaves(spectrum, level) {
        strokeWeight(3);
        noFill();
        
        for (let i = 0; i < 3; i++) {
            stroke(bgHue + i * 30, 70, 80, 70);
            
            beginShape();
            for (let x = -150; x < 150; x += 5) {
                let y = sin(x * 0.01 + frameCount * 0.05 + i * PI/3) * level * 80;
                vertex(x, y);
            }
            endShape();
        }
        
        // Onde centrale réactive au spectre
        stroke(bgHue, 90, 95);
        strokeWeight(5);
        beginShape();
        for (let x = -150; x < 150; x += 3) {
            let freq = spectrum[floor(map(x + 150, 0, 300, 0, spectrum.length))];
            let y = map(freq, 0, 255, -30, -100) * level;
            vertex(x, y);
        }
        endShape();
    }

    drawParticles(level) {
        for (let particle of particleSystem) {
            particle.update(level);
            particle.draw();
        }
        
        if (level > 0.3 && particleSystem.length < 100) {
            particleSystem.push(new AudioParticle());
        }
        
        particleSystem = particleSystem.filter(p => p.alive);
    }

    drawSpectrum(spectrum, level) {
        let binWidth = 300 / (spectrum.length / 4);
        
        for (let i = 0; i < spectrum.length / 4; i++) {
            let x = map(i, 0, spectrum.length / 4, -150, 150);
            let h = map(spectrum[i], 0, 255, 0, 150);
            
            fill(map(i, 0, spectrum.length / 4, 0, 360), 70, 90, 80);
            noStroke();
            rect(x - binWidth/2, 0, binWidth, -h);
            rect(x - binWidth/2, 0, binWidth, h);
        }
    }

    drawControlBar() {
        // Barre de contrôle style Winamp VRAIE avec VRAIS boutons
        let barHeight = 120;
        let barY = height - barHeight;
        
        // Fond de la barre
        fill(0, 0, 20, 95);
        stroke(bgHue, 50, 70);
        strokeWeight(2);
        rect(0, barY, width, barHeight);
        
        // Info du track actuel
        if (currentTrackIndex >= 0 && playlist[currentTrackIndex]) {
            let track = playlist[currentTrackIndex];
            fill(bgHue, 80, 100);
            textAlign(LEFT, CENTER);
            textSize(12);
            text(`🎵 ${track.title}`, 20, barY + 15);
            
            fill(0, 0, 70);
            textSize(10);
            text(`🏷️ ${track.keywords.join(' • ')}`, 20, barY + 30);
        }
        
        // VRAIS BOUTONS de contrôle avec zones tactiles
        this.drawRealPlaybackControls(barY);
        
        // Barre de progression TACTILE
        this.drawTouchProgressBar(barY + 80);
        
        // Boutons playlist et mode
        this.drawSideButtons(barY);
    }

    drawRealPlaybackControls(barY) {
        let buttonY = barY + 50;
        let buttonSize = 40;
        let centerX = width / 2;
        
        // Style boutons réels
        let buttonStyle = {
            normal: { fill: [0, 0, 40], stroke: [bgHue, 40, 70], strokeWeight: 2 },
            hover: { fill: [bgHue, 30, 60], stroke: [bgHue, 60, 90], strokeWeight: 3 },
            active: { fill: [bgHue, 50, 80], stroke: [bgHue, 80, 100], strokeWeight: 3 }
        };
        
        // Zone tactile élargie pour mobile
        let touchPadding = 20;
        
        // Bouton PRÉCÉDENT
        let prevX = centerX - 80;
        let isPrevHover = this.isInTouchZone(prevX, buttonY, buttonSize + touchPadding);
        let prevStyle = isPrevHover ? buttonStyle.hover : buttonStyle.normal;
        
        fill(...prevStyle.fill);
        stroke(...prevStyle.stroke);
        strokeWeight(prevStyle.strokeWeight);
        rect(prevX - buttonSize/2, buttonY - buttonSize/2, buttonSize, buttonSize, 8);
        
        fill(255);
        textAlign(CENTER, CENTER);
        textSize(20);
        text("⏮", prevX, buttonY);
        
        // Bouton PLAY/PAUSE (plus grand)
        let playSize = buttonSize + 10;
        let playX = centerX;
        let isPlayHover = this.isInTouchZone(playX, buttonY, playSize + touchPadding);
        let playStyle = isPlayHover ? buttonStyle.hover : buttonStyle.normal;
        
        if (isPlaying) playStyle = buttonStyle.active;
        
        fill(...playStyle.fill);
        stroke(...playStyle.stroke);
        strokeWeight(playStyle.strokeWeight);
        rect(playX - playSize/2, buttonY - playSize/2, playSize, playSize, 10);
        
        fill(255);
        textSize(24);
        text(isPlaying ? "⏸" : "▶", playX, buttonY);
        
        // Bouton SUIVANT  
        let nextX = centerX + 80;
        let isNextHover = this.isInTouchZone(nextX, buttonY, buttonSize + touchPadding);
        let nextStyle = isNextHover ? buttonStyle.hover : buttonStyle.normal;
        
        fill(...nextStyle.fill);
        stroke(...nextStyle.stroke);
        strokeWeight(nextStyle.strokeWeight);
        rect(nextX - buttonSize/2, buttonY - buttonSize/2, buttonSize, buttonSize, 8);
        
        fill(255);
        textSize(20);
        text("⏭", nextX, buttonY);
        
        // Bouton STOP
        let stopX = centerX + 140;
        let isStopHover = this.isInTouchZone(stopX, buttonY, buttonSize + touchPadding);
        let stopStyle = isStopHover ? buttonStyle.hover : buttonStyle.normal;
        
        fill(...stopStyle.fill);
        stroke(...stopStyle.stroke);
        strokeWeight(stopStyle.strokeWeight);
        rect(stopX - buttonSize/2, buttonY - buttonSize/2, buttonSize, buttonSize, 8);
        
        fill(255);
        textSize(20);
        text("⏹", stopX, buttonY);
        
        // Stockage des zones pour la détection tactile
        this.touchZones = {
            prev: { x: prevX, y: buttonY, size: buttonSize + touchPadding },
            play: { x: playX, y: buttonY, size: playSize + touchPadding },
            next: { x: nextX, y: buttonY, size: buttonSize + touchPadding },
            stop: { x: stopX, y: buttonY, size: buttonSize + touchPadding }
        };
    }

    drawTouchProgressBar(barY) {
        if (!isLoaded || duration === 0) return;
        
        let barWidth = width - 40;
        let barHeight = 12;
        let barX = 20;
        
        // Zone tactile plus large pour mobile
        let touchHeight = 30;
        let touchY = barY - (touchHeight - barHeight) / 2;
        
        // Fond tactile invisible
        fill(0, 0, 0, 1);
        rect(barX - 10, touchY, barWidth + 20, touchHeight);
        
        // Barre de fond
        fill(0, 0, 30);
        stroke(0, 0, 50);
        rect(barX, barY, barWidth, barHeight, 6);
        
        // Barre de progression
        let progress = currentTime / duration;
        fill(bgHue, 70, 90);
        noStroke();
        rect(barX, barY, barWidth * progress, barHeight, 6);
        
        // Curseur tactile (plus gros pour mobile)
        let cursorX = barX + barWidth * progress;
        fill(bgHue, 90, 100);
        stroke(0, 0, 100);
        strokeWeight(2);
        ellipse(cursorX, barY + barHeight/2, 20);
        
        // Temps
        fill(0, 0, 90);
        textAlign(LEFT, CENTER);
        textSize(10);
        text(this.formatTime(currentTime), barX, barY - 15);
        
        textAlign(RIGHT, CENTER);
        text(this.formatTime(duration), barX + barWidth, barY - 15);
        
        // Zone tactile pour la progression
        this.progressBarZone = {
            x: barX - 10,
            y: touchY,
            width: barWidth + 20,
            height: touchHeight,
            barX: barX,
            barWidth: barWidth
        };
    }

    drawSideButtons(barY) {
        let buttonY = barY + 15;
        let buttonSize = 30;
        
        // Bouton playlist (style tactile)
        let playlistX = width - 180;
        let isPlaylistHover = this.isInTouchZone(playlistX, buttonY, buttonSize + 10);
        
        fill(showPlaylist ? [bgHue, 50, 70] : [0, 0, 40]);
        stroke(isPlaylistHover ? [bgHue, 60, 90] : [bgHue, 30, 60]);
        strokeWeight(isPlaylistHover ? 3 : 2);
        rect(playlistX - buttonSize/2, buttonY - buttonSize/2, buttonSize, buttonSize, 6);
        
        fill(255);
        textAlign(CENTER, CENTER);
        textSize(10);
        text("LIST", playlistX, buttonY);
        
        // Bouton mode visualisation
        let modeX = width - 120;
        let isModeHover = this.isInTouchZone(modeX, buttonY, buttonSize + 10);
        
        fill(0, 0, 40);
        stroke(isModeHover ? [bgHue, 60, 90] : [bgHue, 30, 60]);
        strokeWeight(isModeHover ? 3 : 2);
        rect(modeX - buttonSize/2, buttonY - buttonSize/2, buttonSize, buttonSize, 6);
        
        fill(255);
        let modeIcon = {
            'waves': '〰',
            'particles': '✦', 
            'spectrum': '▬',
            'spider': '◇'
        }[visualMode] || '?';
        text(modeIcon, modeX, buttonY);
        
        // Stockage zones tactiles
        this.sideButtons = {
            playlist: { x: playlistX, y: buttonY, size: buttonSize + 10 },
            mode: { x: modeX, y: buttonY, size: buttonSize + 10 }
        };
    }

    // Utilitaire de détection tactile
    isInTouchZone(x, y, size) {
        return dist(mouseX, mouseY, x, y) < size/2;
    }

    drawPlaceholder() {
        fill(0, 0, 60);
        textAlign(CENTER, CENTER);
        textSize(24);
        text("🎵", width/2, height/2 - 40);
        textSize(16);
        fill(0, 0, 40);
        text("Créez votre première phrase", width/2, height/2 - 10);
        text("pour démarrer la playlist !", width/2, height/2 + 20);
    }

    formatTime(seconds) {
        let mins = floor(seconds / 60);
        let secs = floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    // === MÉTHODES D'AIDE POUR LES ZONES TACTILES ===
    
    isInZone(x, y, zone) {
        if (!zone) return false;
        return dist(x, y, zone.x, zone.y) < zone.size / 2;
    }
    
    isInRectZone(x, y, zone) {
        if (!zone) return false;
        return x >= zone.x && x <= zone.x + zone.width &&
               y >= zone.y && y <= zone.y + zone.height;
    }

    handleMousePressed() {
        // Gestion TACTILE pour mobile et desktop
        this.handleTouchStart(mouseX, mouseY);
    }
    
    handleTouchStart(x, y) {
        console.log(`👆 Touch/Click: ${x}, ${y}`);
        
        // Gestion des modes visuels
        if (this.visualModeZones) {
            for (let mode in this.visualModeZones) {
                let zone = this.visualModeZones[mode];
                if (this.isInRectZone(x, y, zone)) {
                    visualMode = mode;
                    console.log(`🎨 Mode visuel: ${mode}`);
                    return;
                }
            }
        }
        
        // NOUVEAU: Contrôles compacts en haut
        if (this.controlZones) {
            // Bouton PLAY/PAUSE compact
            if (this.isInZone(x, y, this.controlZones.play)) {
                this.togglePlay();
                this.addTouchFeedback(this.controlZones.play.x, this.controlZones.play.y);
                return;
            }
            
            // Bouton PRÉCÉDENT compact
            if (this.isInZone(x, y, this.controlZones.prev)) {
                this.prevTrack();
                this.addTouchFeedback(this.controlZones.prev.x, this.controlZones.prev.y);
                return;
            }
            
            // Bouton SUIVANT compact
            if (this.isInZone(x, y, this.controlZones.next)) {
                this.nextTrack();
                this.addTouchFeedback(this.controlZones.next.x, this.controlZones.next.y);
                return;
            }
        }
        
        // Gestion de la playlist
        if (this.playlistZones) {
            for (let i = 0; i < this.playlistZones.length; i++) {
                let zone = this.playlistZones[i];
                if (zone && this.isInRectZone(x, y, zone)) {
                    this.playTrack(zone.index);
                    console.log(`🎵 Lecture track: ${zone.index}`);
                    return;
                }
            }
        }
        
        // Contrôles principaux (ancienne version - fallback)
        if (this.touchZones) {
            // Bouton PLAY/PAUSE
            if (this.isPointInZone(x, y, this.touchZones.play)) {
                this.togglePlay();
                this.addTouchFeedback(this.touchZones.play.x, this.touchZones.play.y);
                return;
            }
            
            // Bouton PRÉCÉDENT
            if (this.isPointInZone(x, y, this.touchZones.prev)) {
                this.prevTrack();
                this.addTouchFeedback(this.touchZones.prev.x, this.touchZones.prev.y);
                return;
            }
            
            // Bouton SUIVANT
            if (this.isPointInZone(x, y, this.touchZones.next)) {
                this.nextTrack();
                this.addTouchFeedback(this.touchZones.next.x, this.touchZones.next.y);
                return;
            }
            
            // Bouton STOP
            if (this.isPointInZone(x, y, this.touchZones.stop)) {
                this.stopPlayback();
                this.addTouchFeedback(this.touchZones.stop.x, this.touchZones.stop.y);
                return;
            }
        }
        
        // Barre de progression TACTILE
        if (this.progressBarZone && this.isPointInProgressBar(x, y)) {
            this.handleProgressBarTouch(x);
            return;
        }
        
        // Boutons latéraux (playlist, mode)
        if (this.sideButtons) {
            // Bouton playlist
            if (this.isPointInZone(x, y, this.sideButtons.playlist)) {
                showPlaylist = !showPlaylist;
                this.addTouchFeedback(this.sideButtons.playlist.x, this.sideButtons.playlist.y);
                return;
            }
            
            // Bouton mode
            if (this.isPointInZone(x, y, this.sideButtons.mode)) {
                this.cycleVisualMode();
                this.addTouchFeedback(this.sideButtons.mode.x, this.sideButtons.mode.y);
                return;
            }
        }
        
        // Interactions avec la playlist
        if (showPlaylist && this.playlistTouchZones) {
            this.handlePlaylistTouch(x, y);
            return;
        }
    }
    
    isPointInZone(x, y, zone) {
        return dist(x, y, zone.x, zone.y) < zone.size/2;
    }
    
    isPointInProgressBar(x, y) {
        let zone = this.progressBarZone;
        return x >= zone.x && x <= zone.x + zone.width && 
               y >= zone.y && y <= zone.y + zone.height;
    }
    
    handleProgressBarTouch(x) {
        if (!isLoaded || duration === 0 || !audioPlayer) return;
        
        let zone = this.progressBarZone;
        let progress = (x - zone.barX) / zone.barWidth;
        progress = constrain(progress, 0, 1);
        
        let newTime = progress * duration;
        
        // Utiliser l'API p5.js pour changer le temps
        audioPlayer.jump(newTime);
        currentTime = newTime;
        
        // Feedback tactile
        this.addTouchFeedback(x, zone.y + zone.height/2);
        console.log('⏭️ Saut à:', this.formatTime(newTime));
    }
    
    handlePlaylistTouch(x, y) {
        // Vérifier les boutons de chaque track
        if (this.trackButtonZones) {
            for (let i = 0; i < this.trackButtonZones.length; i++) {
                let buttons = this.trackButtonZones[i];
                
                // Bouton play du track
                if (buttons.play && dist(x, y, buttons.play.x, buttons.play.y) < buttons.play.size/2) {
                    if (i === currentTrackIndex) {
                        this.togglePlay();
                    } else {
                        this.playTrack(i);
                    }
                    this.addTouchFeedback(buttons.play.x, buttons.play.y);
                    return;
                }
                
                // Bouton delete du track
                if (buttons.delete && dist(x, y, buttons.delete.x, buttons.delete.y) < buttons.delete.size/2) {
                    this.removeTrack(i);
                    this.addTouchFeedback(buttons.delete.x, buttons.delete.y);
                    return;
                }
            }
        }
        
        // Clic sur track entier pour le sélectionner
        if (this.playlistTouchZones) {
            for (let zone of this.playlistTouchZones) {
                if (x >= zone.x && x <= zone.x + zone.width && 
                    y >= zone.y && y <= zone.y + zone.height) {
                    this.playTrack(zone.index);
                    this.addTouchFeedback(zone.x + zone.width/2, zone.y + zone.height/2);
                    return;
                }
            }
        }
    }
    
    addTouchFeedback(x, y) {
        // Effet visuel de touch/clic
        // TODO: Ajouter des ondulations ou flash
        
        // Vibration mobile si disponible
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
    }
    
    cycleVisualMode() {
        let modes = ['waves', 'particles', 'spectrum', 'spider'];
        let currentIndex = modes.indexOf(visualMode);
        visualMode = modes[(currentIndex + 1) % modes.length];
        console.log('🎨 Mode visualisation:', visualMode);
    }
    
    removeTrack(index) {
        if (index < 0 || index >= playlist.length) return;
        
        // Si on supprime le track en cours, stopper
        if (index === currentTrackIndex) {
            this.stopPlayback();
            currentTrackIndex = -1;
        } else if (index < currentTrackIndex) {
            // Ajuster l'index si on supprime avant le track actuel
            currentTrackIndex--;
        }
        
        // Supprimer de la playlist
        playlist.splice(index, 1);
        
        // Nettoyer les zones tactiles
        if (this.playlistTouchZones) {
            this.playlistTouchZones.splice(index, 1);
        }
        if (this.trackButtonZones) {
            this.trackButtonZones.splice(index, 1);
        }
        
        console.log(`🗑️ Track ${index + 1} supprimé de la playlist`);
    }
    
    // Utilitaire pour ajuster le volume (API p5.js)
    setVolume(volume) {
        if (audioPlayer) {
            audioPlayer.setVolume(constrain(volume, 0, 1));
        }
    }

    togglePlay() {
        if (!audioPlayer || !isLoaded) return;
        
        // IMPORTANT: S'assurer que l'AudioContext est activé sur mobile
        if (getAudioContext && getAudioContext().state === 'suspended') {
            console.log('📱 Activation AudioContext au clic...');
            getAudioContext().resume().then(() => {
                console.log('✅ AudioContext activé, lecture...');
                this.actualPlay();
            });
        } else {
            this.actualPlay();
        }
    }
    
    actualPlay() {
        if (isPlaying) {
            audioPlayer.pause();
            isPlaying = false;
            console.log('⏸️ Audio mis en pause');
        } else {
            audioPlayer.play();
            isPlaying = true;
            console.log('▶️ Audio en lecture');
        }
    }
    
    stopPlayback() {
        if (audioPlayer) {
            audioPlayer.stop();
            isPlaying = false;
            currentTime = 0;
            console.log('⏹️ Audio arrêté');
        }
    }
    
    // Vérification du statut de lecture dans draw()
    updatePlaybackStatus() {
        if (audioPlayer && isLoaded) {
            // p5.js met à jour automatiquement currentTime via currentTime()
            if (isPlaying) {
                currentTime = audioPlayer.currentTime();
                
                // Vérifier si le track est terminé
                if (currentTime >= duration - 0.1) {
                    isPlaying = false;
                    console.log('🏁 Track terminé, passage au suivant');
                    setTimeout(() => this.nextTrack(), 1000);
                }
            }
        }
    }
}

// Classe pour les particules audio-réactives (inchangée)
class AudioParticle {
    constructor() {
        this.reset();
        this.age = 0;
        this.maxAge = 120;
        this.alive = true;
    }
    
    reset() {
        this.x = random(-150, 150);
        this.y = random(-150, 150);
        this.vx = random(-2, 2);
        this.vy = random(-2, 2);
        this.size = random(3, 8);
        this.hue = random(360);
    }
    
    update(audioLevel) {
        this.vx += random(-0.5, 0.5) * audioLevel;
        this.vy += random(-0.5, 0.5) * audioLevel;
        
        this.x += this.vx * (1 + audioLevel);
        this.y += this.vy * (1 + audioLevel);
        
        let centerForce = 0.02 * audioLevel;
        this.vx -= this.x * centerForce;
        this.vy -= this.y * centerForce;
        
        this.vx *= 0.98;
        this.vy *= 0.98;
        
        this.age++;
        if (this.age > this.maxAge) {
            this.alive = false;
        }
        
        this.size = this.size + audioLevel * 3;
    }
    
    draw() {
        let alpha = map(this.age, 0, this.maxAge, 100, 0);
        fill(this.hue, 70, 90, alpha);
        noStroke();
        ellipse(this.x, this.y, this.size);
        
        fill(this.hue, 50, 70, alpha * 0.3);
        ellipse(this.x - this.vx * 3, this.y - this.vy * 3, this.size * 0.6);
    }
    
    // === MÉTHODES DE VISUALISATION RESTAURÉES ===
    
    drawSpectrumVisualization(startY, height, level) {
        // Analyse spectrale avec FFT
        let spectrum = fft.analyze();
        let barWidth = (width - 60) / (spectrum.length / 8); // Moins de barres pour plus de clarté
        
        push();
        translate(30, startY + height/2);
        
        // Dessiner les barres du spectrum
        for (let i = 0; i < spectrum.length / 8; i++) {
            let amp = spectrum[i];
            let barHeight = map(amp, 0, 255, 5, height/2 - 20);
            
            // Couleurs arc-en-ciel basées sur la fréquence
            let hue = map(i, 0, spectrum.length / 8, bgHue - 60, bgHue + 60);
            let saturation = map(amp, 0, 255, 40, 90);
            let brightness = map(amp, 0, 255, 50, 95);
            
            fill(hue, saturation, brightness, 85);
            noStroke();
            
            let x = i * barWidth;
            rect(x, 0, barWidth - 2, -barHeight); // Barre vers le haut
            
            // Effet miroir vers le bas
            fill(hue, saturation, brightness, 40);
            rect(x, 0, barWidth - 2, barHeight / 3);
        }
        
        pop();
    }
    
    drawParticleVisualization(startY, height, level) {
        // Animation de particules audio-réactives
        let spectrum = fft.analyze();
        
        // Mettre à jour les particules existantes
        for (let i = 0; i < particleSystem.length; i++) {
            let particle = particleSystem[i];
            
            // Influence de l'audio sur la particule
            let spectrumIndex = Math.floor(map(i, 0, particleSystem.length, 0, spectrum.length));
            let audioInfluence = map(spectrum[spectrumIndex], 0, 255, 0.5, 3);
            
            particle.update(level * audioInfluence);
            particle.display(startY + height/2, height);
        }
        
        // Ajouter des particules si forte amplitude
        if (level > 0.7 && particleSystem.length < 80) {
            particleSystem.push(new AudioParticle());
        }
        
        // Info visualisation
        fill(bgHue, 60, 80);
        textAlign(CENTER, TOP);
        textSize(12);
        text(`${particleSystem.length} particules • Niveau: ${(level * 100).toFixed(0)}%`, 
             width/2, startY + 10);
    }
    
    drawWaveVisualization(startY, height, level) {
        // Forme d'onde basée sur l'amplitude
        let waveform = fft.waveform();
        
        push();
        translate(30, startY + height/2);
        
        // Configuration d'onde
        stroke(bgHue, 80, 90);
        strokeWeight(3);
        noFill();
        
        // Dessiner l'onde
        beginShape();
        for (let i = 0; i < waveform.length; i += 4) { // Échantillonner moins pour performance
            let x = map(i, 0, waveform.length, 0, width - 60);
            let y = map(waveform[i], -1, 1, -height/3, height/3);
            vertex(x, y);
        }
        endShape();
        
        // Onde secondaire avec phase décalée
        stroke(bgHue, 60, 70, 60);
        strokeWeight(2);
        beginShape();
        for (let i = 0; i < waveform.length; i += 6) {
            let x = map(i, 0, waveform.length, 0, width - 60);
            let y = map(waveform[i], -1, 1, -height/4, height/4) + sin(millis() * 0.01 + i * 0.1) * 10;
            vertex(x, y);
        }
        endShape();
        
        pop();
        
        // Indicateurs
        fill(bgHue, 70, 85);
        textAlign(LEFT, TOP);
        textSize(10);
        text(`Forme d'onde • ${waveform.length} échantillons`, 40, startY + height - 20);
    }
    
    drawSpiderVisualization(startY, height, level) {
        // Graphique radar/spider des émotions
        if (!spiderData) {
            // Données par défaut si pas de spider data
            spiderData = {
                'Passion': Math.random() * 0.6 + 0.4,
                'Tendresse': Math.random() * 0.5 + 0.3,
                'Désir': Math.random() * 0.7 + 0.3,
                'Romance': Math.random() * 0.8 + 0.2,
                'Mélancolie': Math.random() * 0.4 + 0.2,
                'Espoir': Math.random() * 0.6 + 0.4,
                'Sensualité': Math.random() * 0.5 + 0.3,
                'Poésie': Math.random() * 0.9 + 0.1
            };
        }
        
        push();
        translate(width/2, startY + height/2);
        
        let categories = Object.keys(spiderData);
        let angleStep = TWO_PI / categories.length;
        let maxRadius = Math.min(height, width) / 4;
        
        // Grille de fond (cercles concentriques)
        stroke(bgHue, 20, 60, 30);
        strokeWeight(1);
        noFill();
        for (let r = maxRadius / 4; r <= maxRadius; r += maxRadius / 4) {
            ellipse(0, 0, r * 2);
        }
        
        // Lignes radiales
        for (let i = 0; i < categories.length; i++) {
            let angle = i * angleStep - PI/2;
            let x = cos(angle) * maxRadius;
            let y = sin(angle) * maxRadius;
            line(0, 0, x, y);
        }
        
        // Tracé des données avec effet audio
        let audioBoost = 1 + level * 0.5; // Boost audio-réactif
        
        fill(bgHue, 70, 80, 40);
        stroke(bgHue, 90, 100);
        strokeWeight(2);
        
        beginShape();
        for (let i = 0; i < categories.length; i++) {
            let angle = i * angleStep - PI/2;
            let value = spiderData[categories[i]] * audioBoost;
            let radius = value * maxRadius;
            
            let x = cos(angle) * radius;
            let y = sin(angle) * radius;
            vertex(x, y);
        }
        endShape(CLOSE);
        
        // Points et labels
        for (let i = 0; i < categories.length; i++) {
            let angle = i * angleStep - PI/2;
            let value = spiderData[categories[i]] * audioBoost;
            let radius = value * maxRadius;
            
            let x = cos(angle) * radius;
            let y = sin(angle) * radius;
            
            // Point de donnée
            fill(bgHue, 100, 100);
            noStroke();
            ellipse(x, y, 6);
            
            // Label de catégorie
            let labelX = cos(angle) * (maxRadius + 20);
            let labelY = sin(angle) * (maxRadius + 20);
            
            fill(bgHue, 80, 90);
            textAlign(CENTER, CENTER);
            textSize(10);
            text(categories[i], labelX, labelY);
        }
        
        pop();
        
        // Titre et info
        fill(bgHue, 70, 100);
        textAlign(CENTER, TOP);
        textSize(12);
        text("ANALYSE SÉMANTIQUE ÉMOTIONNELLE", width/2, startY + 5);
    }
}
}

// Instance globale
let visualizer;

function setup() {
    // Cette fonction sera appelée automatiquement par p5.js
}

function draw() {
    if (visualizer) {
        visualizer.draw();
    }
}

// Définir le gestionnaire de clic global pour p5.js
if (typeof window !== 'undefined') {
    window.mousePressed = function() {
        if (visualizer) {
            visualizer.handleMousePressed();
        }
        // Ne pas empêcher le comportement par défaut pour permettre le scroll
    };
    
    // Support tactile mobile SANS bloquer le scroll
    window.touchStarted = function() {
        if (visualizer && touches.length === 1) {
            // Seulement gérer les touches simples (pas le pinch/scroll)
            const touch = touches[0];
            visualizer.handleTouchStart(touch.x, touch.y);
        }
        // IMPORTANT: Retourner true pour permettre le scroll natif
        return true;
    };
    
    window.touchEnded = function() {
        // Permettre le comportement par défaut (scroll, etc.)
        return true;
    };
    
    window.touchMoved = function() {
        // Permettre le scroll natif
        return true;
    };
}

function onP5MousePressed() {
    if (visualizer) {
        visualizer.handleMousePressed();
    }
}

// Fonctions pour l'interface principale
function initAudioVisualizer() {
    console.log('🎵 Initialisation du visualisateur audio...');
    
    if (typeof p5 === 'undefined') {
        console.error('❌ p5.js non chargé !');
        return false;
    }
    
    // Vérifier les composants p5.sound essentiels
    if (typeof p5.Amplitude === 'undefined') {
        console.error('❌ p5.Amplitude non disponible !');
        return false;
    }
    
    if (typeof p5.FFT === 'undefined') {
        console.error('❌ p5.FFT non disponible !');
        return false;
    }
    
    try {
        visualizer = new AudioVisualizer();
        console.log('✅ Visualisateur audio créé avec succès');
        return true;
    } catch (error) {
        console.error('❌ Erreur création visualisateur:', error);
        return false;
    }
}

function addTrackToPlaylist(audioUrl, metadata) {
    if (visualizer) {
        visualizer.addToPlaylist(audioUrl, metadata);
    }
}

// Export pour utilisation dans l'interface principale
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AudioVisualizer, initAudioVisualizer, addTrackToPlaylist };
}