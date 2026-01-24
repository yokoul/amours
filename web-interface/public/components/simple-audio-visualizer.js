// Visualiseur audio simple avec canvas natif (sans p5.js)
class SimpleAudioVisualizer {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.canvas = null;
        this.ctx = null;
        this.audioContext = null;
        this.analyzer = null;
        this.audioSource = null;
        this.isInitialized = false;
        this.animationId = null;
        
        // Options par défaut
        this.options = {
            width: options.width || 400,
            height: options.height || 200,
            fftSize: options.fftSize || 256,
            smoothingTimeConstant: options.smoothingTimeConstant || 0.8,
            barColor: options.barColor || '#ff6b9d',
            backgroundColor: options.backgroundColor || 'rgba(0, 0, 0, 0.1)',
            showFrequencyLabels: options.showFrequencyLabels !== false
        };
        
        this.init();
    }
    
    init() {
        this.createCanvas();
        this.setupAudioContext();
        console.log('📊 Visualiseur audio simple initialisé');
    }
    
    createCanvas() {
        this.container.innerHTML = `
            <div class="simple-visualizer">
                <h4>📊 Analyse Spectrale</h4>
                <div class="visualizer-controls">
                    <button id="viz-play" class="viz-btn" disabled>▶</button>
                    <button id="viz-pause" class="viz-btn" disabled>⏸</button>
                    <select id="viz-mode" class="viz-select">
                        <option value="bars">Barres</option>
                        <option value="wave">Onde</option>
                        <option value="circle">Circulaire</option>
                    </select>
                </div>
                <canvas id="viz-canvas" width="${this.options.width}" height="${this.options.height}"></canvas>
                <div class="visualizer-info" id="viz-info">
                    <span class="frequency-info">Fréquence: En attente</span>
                    <span class="amplitude-info">Amplitude: 0%</span>
                </div>
            </div>
        `;
        
        this.canvas = this.container.querySelector('#viz-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.playBtn = this.container.querySelector('#viz-play');
        this.pauseBtn = this.container.querySelector('#viz-pause');
        this.modeSelect = this.container.querySelector('#viz-mode');
        this.infoDiv = this.container.querySelector('#viz-info');
        
        // Configuration canvas haute résolution
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();
        
        this.canvas.width = this.options.width * dpr;
        this.canvas.height = this.options.height * dpr;
        this.ctx.scale(dpr, dpr);
        
        // Événements
        this.attachEvents();
    }
    
    attachEvents() {
        this.playBtn.addEventListener('click', () => this.startVisualization());
        this.pauseBtn.addEventListener('click', () => this.stopVisualization());
        this.modeSelect.addEventListener('change', (e) => {
            this.visualizationMode = e.target.value;
        });
        
        // Gérer le redimensionnement
        window.addEventListener('resize', () => {
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => {
                this.resizeCanvas();
            }, 250);
        });
    }
    
    resizeCanvas() {
        // Reconfigurer le canvas pour la nouvelle taille
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();
        
        // Ajuster les dimensions en fonction de l'écran
        const containerWidth = this.container.clientWidth;
        let newWidth, newHeight;
        
        if (window.innerWidth <= 480) {
            newWidth = Math.min(containerWidth - 20, 350);
            newHeight = 120;
        } else if (window.innerWidth <= 768) {
            newWidth = Math.min(containerWidth - 30, 400);
            newHeight = 150;
        } else {
            newWidth = this.options.width;
            newHeight = this.options.height;
        }
        
        this.canvas.width = newWidth * dpr;
        this.canvas.height = newHeight * dpr;
        this.canvas.style.width = newWidth + 'px';
        this.canvas.style.height = newHeight + 'px';
        this.ctx.scale(dpr, dpr);
        
        // Mise à jour des dimensions internes
        this.options.width = newWidth;
        this.options.height = newHeight;
    }
    
    async setupAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyzer = this.audioContext.createAnalyser();
            
            this.analyzer.fftSize = this.options.fftSize;
            this.analyzer.smoothingTimeConstant = this.options.smoothingTimeConstant;
            
            this.bufferLength = this.analyzer.frequencyBinCount;
            this.dataArray = new Uint8Array(this.bufferLength);
            this.waveformArray = new Uint8Array(this.analyzer.fftSize);
            
            console.log('🎵 Contexte audio configuré');
        } catch (error) {
            console.error('❌ Erreur configuration audio:', error);
        }
    }
    
    connectToAudioElement(audioElement) {
        if (!this.audioContext || !audioElement) return;
        
        try {
            // Vérifier si cet élément audio a déjà une source associée
            if (audioElement._audioSourceConnected) {
                console.log('🔗 Élément audio déjà connecté, réutilisation de la source existante');
                return;
            }
            
            // Déconnecter source précédente si elle existe
            if (this.audioSource) {
                this.audioSource.disconnect();
            }
            
            // Créer nouvelle source
            this.audioSource = this.audioContext.createMediaElementSource(audioElement);
            this.audioSource.connect(this.analyzer);
            this.analyzer.connect(this.audioContext.destination);
            
            // Marquer cet élément comme connecté
            audioElement._audioSourceConnected = true;
            
            this.isInitialized = true;
            this.enableControls();
            
            console.log('🔗 Audio connecté au visualiseur');
        } catch (error) {
            console.error('❌ Erreur connexion audio:', error);
            // Si l'erreur est due à une connexion existante, on continue quand même
            if (error.name === 'InvalidStateError') {
                console.log('⚠️ Source audio déjà connectée, on continue...');
                audioElement._audioSourceConnected = true;
                this.isInitialized = true;
                this.enableControls();
            }
        }
    }
    
    enableControls() {
        this.playBtn.disabled = false;
        this.pauseBtn.disabled = false;
    }
    
    startVisualization() {
        if (!this.isInitialized) {
            console.warn('⚠️ Visualiseur non initialisé');
            return;
        }
        
        // Reprendre le contexte audio si suspendu (mobile)
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
        
        this.visualizationMode = this.modeSelect.value;
        this.animate();
        
        console.log('▶ Visualisation démarrée');
    }
    
    stopVisualization() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        
        // Effacer le canvas
        this.ctx.clearRect(0, 0, this.options.width, this.options.height);
        this.drawBackground();
        
        console.log('⏸ Visualisation arrêtée');
    }
    
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        // Obtenir les données audio
        this.analyzer.getByteFrequencyData(this.dataArray);
        this.analyzer.getByteTimeDomainData(this.waveformArray);
        
        // Effacer et redessiner
        this.ctx.clearRect(0, 0, this.options.width, this.options.height);
        this.drawBackground();
        
        // Dessiner selon le mode sélectionné
        switch (this.visualizationMode) {
            case 'bars':
                this.drawBars();
                break;
            case 'wave':
                this.drawWaveform();
                break;
            case 'circle':
                this.drawCircular();
                break;
            default:
                this.drawBars();
        }
        
        // Mettre à jour les infos
        this.updateInfo();
    }
    
    drawBackground() {
        this.ctx.fillStyle = this.options.backgroundColor;
        this.ctx.fillRect(0, 0, this.options.width, this.options.height);
        
        // Grille optionnelle
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
        this.ctx.lineWidth = 1;
        
        // Lignes horizontales
        for (let y = 0; y < this.options.height; y += 50) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.options.width, y);
            this.ctx.stroke();
        }
    }
    
    drawBars() {
        const barWidth = this.options.width / this.bufferLength * 2;
        let x = 0;
        
        for (let i = 0; i < this.bufferLength; i++) {
            const barHeight = (this.dataArray[i] / 255) * this.options.height * 0.8;
            
            // Gradient de couleur basé sur la fréquence
            const hue = (i / this.bufferLength) * 360;
            const saturation = 70 + (this.dataArray[i] / 255) * 30;
            const lightness = 50 + (this.dataArray[i] / 255) * 30;
            
            this.ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
            this.ctx.fillRect(x, this.options.height - barHeight, barWidth, barHeight);
            
            // Effet de réflexion
            const gradient = this.ctx.createLinearGradient(0, this.options.height, 0, this.options.height - barHeight/3);
            gradient.addColorStop(0, `hsla(${hue}, ${saturation}%, ${lightness}%, 0.3)`);
            gradient.addColorStop(1, `hsla(${hue}, ${saturation}%, ${lightness}%, 0)`);
            
            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(x, this.options.height - barHeight/3, barWidth, barHeight/3);
            
            x += barWidth + 1;
        }
    }
    
    drawWaveform() {
        this.ctx.lineWidth = 3;
        this.ctx.strokeStyle = this.options.barColor;
        this.ctx.beginPath();
        
        const sliceWidth = this.options.width / this.waveformArray.length;
        let x = 0;
        
        for (let i = 0; i < this.waveformArray.length; i++) {
            const v = this.waveformArray[i] / 128.0;
            const y = v * this.options.height / 2;
            
            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
            
            x += sliceWidth;
        }
        
        this.ctx.lineTo(this.options.width, this.options.height / 2);
        this.ctx.stroke();
        
        // Onde secondaire décalée
        this.ctx.lineWidth = 2;
        this.ctx.strokeStyle = this.options.barColor + '80';
        this.ctx.beginPath();
        
        x = 0;
        for (let i = 0; i < this.waveformArray.length; i += 2) {
            const v = this.waveformArray[i] / 128.0;
            const y = v * this.options.height / 3 + this.options.height / 2;
            
            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
            
            x += sliceWidth * 2;
        }
        
        this.ctx.stroke();
    }
    
    drawCircular() {
        const centerX = this.options.width / 2;
        const centerY = this.options.height / 2;
        const maxRadius = Math.min(centerX, centerY) - 20;
        
        // Cercle de base
        this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, maxRadius * 0.3, 0, Math.PI * 2);
        this.ctx.stroke();
        
        // Barres circulaires
        const angleStep = (Math.PI * 2) / this.bufferLength;
        
        for (let i = 0; i < this.bufferLength; i++) {
            const angle = i * angleStep;
            const barHeight = (this.dataArray[i] / 255) * maxRadius * 0.6;
            
            const innerRadius = maxRadius * 0.3;
            const outerRadius = innerRadius + barHeight;
            
            const x1 = centerX + Math.cos(angle) * innerRadius;
            const y1 = centerY + Math.sin(angle) * innerRadius;
            const x2 = centerX + Math.cos(angle) * outerRadius;
            const y2 = centerY + Math.sin(angle) * outerRadius;
            
            // Couleur basée sur la fréquence et l'amplitude
            const hue = (i / this.bufferLength) * 360;
            const alpha = 0.6 + (this.dataArray[i] / 255) * 0.4;
            
            this.ctx.strokeStyle = `hsla(${hue}, 70%, 60%, ${alpha})`;
            this.ctx.lineWidth = 2;
            this.ctx.beginPath();
            this.ctx.moveTo(x1, y1);
            this.ctx.lineTo(x2, y2);
            this.ctx.stroke();
        }
    }
    
    updateInfo() {
        // Calculer l'amplitude moyenne
        const avgAmplitude = this.dataArray.reduce((sum, val) => sum + val, 0) / this.dataArray.length;
        const amplitudePercent = Math.round((avgAmplitude / 255) * 100);
        
        // Trouver la fréquence dominante
        let maxIndex = 0;
        let maxValue = 0;
        for (let i = 0; i < this.dataArray.length; i++) {
            if (this.dataArray[i] > maxValue) {
                maxValue = this.dataArray[i];
                maxIndex = i;
            }
        }
        
        const dominantFreq = Math.round((maxIndex / this.bufferLength) * (this.audioContext.sampleRate / 2));
        
        // Mettre à jour l'affichage
        const freqInfo = this.container.querySelector('.frequency-info');
        const ampInfo = this.container.querySelector('.amplitude-info');
        
        if (freqInfo) freqInfo.textContent = `Fréquence dominante: ${dominantFreq} Hz`;
        if (ampInfo) ampInfo.textContent = `Amplitude: ${amplitudePercent}%`;
    }
    
    // API publique
    setAudioElement(audioElement) {
        this.connectToAudioElement(audioElement);
    }
    
    setVisualizationMode(mode) {
        this.visualizationMode = mode;
        this.modeSelect.value = mode;
    }
    
    getFrequencyData() {
        return this.dataArray ? Array.from(this.dataArray) : [];
    }
    
    getWaveformData() {
        return this.waveformArray ? Array.from(this.waveformArray) : [];
    }
    
    destroy() {
        this.stopVisualization();
        if (this.audioSource) {
            this.audioSource.disconnect();
        }
        if (this.audioContext && this.audioContext.state !== 'closed') {
            this.audioContext.close();
        }
    }
}

// Export pour utilisation globale
window.SimpleAudioVisualizer = SimpleAudioVisualizer;