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
        // Créer un canvas plus grand pour accommoder playlist et spider charts
        console.log('🎨 Initialisation du canvas p5.js...');
        
        canvas = createCanvas(800, 600);
        canvas.parent('p5-audio-container');
        
        // IMPORTANT: Permettre le scroll sur mobile
        canvas.style('touch-action', 'manipulation');
        canvas.style('pointer-events', 'auto');
        
        // Initialiser l'analyse audio
        amplitude = new p5.Amplitude();
        fft = new p5.FFT(0.8, 1024);
        
        colorMode(HSB, 360, 100, 100, 100);
        
        // Créer le système de particules initial
        for (let i = 0; i < 50; i++) {
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
        
        this.loadAudio(track.audioUrl);
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

    loadAudio(audioUrl) {
        if (currentAudioUrl === audioUrl) return;
        
        if (audioPlayer) {
            audioPlayer.stop();
            audioPlayer = null;
        }
        
        currentAudioUrl = audioUrl;
        console.log('🎵 Chargement audio p5.js:', audioUrl);
        
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
        
        if (!audioPlayer) {
            this.drawPlaceholder();
            return;
        }
        
        // Mettre à jour le statut de lecture
        this.updatePlaybackStatus();
        
        // Layout : playlist à gauche, visualisation au centre, spider à droite
        this.drawLayout();
    }

    drawLayout() {
        let level = amplitude.getLevel();
        bgHue = (bgHue + level * 30) % 360;
        
        // Zone playlist (gauche)
        if (showPlaylist && playlist.length > 0) {
            this.drawPlaylist();
        }
        
        // Zone visualisation centrale
        push();
        translate(showPlaylist ? width * 0.4 : width * 0.3, height * 0.5);
        this.drawMainVisualization(level);
        pop();
        
        // Zone spider chart (droite)
        if (spiderData && (visualMode === 'spider' || showPlaylist)) {
            this.drawSpiderChart();
        }
        
        // Interface de contrôle en bas
        this.drawControlBar();
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

    handleMousePressed() {
        // Gestion TACTILE pour mobile et desktop
        this.handleTouchStart(mouseX, mouseY);
    }
    
    handleTouchStart(x, y) {
        // Contrôles principaux (play, pause, next, prev, stop)
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