// Visualisations audio canvas simples et performantes
class AudioVisualizer {
    constructor(canvasId, audioPlayer, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.audioPlayer = audioPlayer;
        
        this.options = {
            width: options.width || 800,
            height: options.height || 300,
            mode: options.mode || 'spectrum', // 'spectrum', 'waveform', 'particles'
            colors: options.colors || {
                background: 'rgba(20, 10, 40, 0.9)',
                primary: '#ff64c8',
                secondary: '#ff9ad5',
                accent: '#64ffff'
            }
        };
        
        this.isActive = false;
        this.animationFrame = null;
        this.particles = [];
        
        this.init();
    }
    
    init() {
        this.setupCanvas();
        this.setupAudioContext();
        this.createParticles();
        
        console.log('🎨 AudioVisualizer initialisé');
    }
    
    setupCanvas() {
        this.canvas.width = this.options.width;
        this.canvas.height = this.options.height;
        this.canvas.style.width = `${this.options.width}px`;
        this.canvas.style.height = `${this.options.height}px`;
        
        this.center = {
            x: this.options.width / 2,
            y: this.options.height / 2
        };
    }
    
    setupAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Attendre qu'un audio soit chargé
            this.checkForAudio();
        } catch (error) {
            console.log('🔊 AudioContext pas encore disponible');
        }
    }
    
    checkForAudio() {
        const checkInterval = setInterval(() => {
            if (this.audioPlayer.audioElement && this.audioPlayer.audioElement.src) {
                this.connectAudioSource();
                clearInterval(checkInterval);
            }
        }, 500);
        
        // Arrêter après 10 secondes
        setTimeout(() => clearInterval(checkInterval), 10000);
    }
    
    connectAudioSource() {
        try {
            if (this.audioContext.state === 'suspended') {
                this.audioContext.resume();
            }
            
            // Créer les analyseurs
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.bufferLength = this.analyser.frequencyBinCount;
            this.dataArray = new Uint8Array(this.bufferLength);
            
            // Connecter à l'élément audio
            const source = this.audioContext.createMediaElementSource(this.audioPlayer.audioElement);
            source.connect(this.analyser);
            this.analyser.connect(this.audioContext.destination);
            
            console.log('🔊 Audio connecté au visualizer');
            this.startVisualization();
            
        } catch (error) {
            console.log('⚠️ Erreur connexion audio:', error.message);
        }
    }
    
    createParticles() {
        const numParticles = 50;
        for (let i = 0; i < numParticles; i++) {
            this.particles.push(new SimpleParticle(this.options.width, this.options.height));
        }
    }
    
    startVisualization() {
        if (this.isActive) return;
        
        this.isActive = true;
        this.animate();
    }
    
    stopVisualization() {
        this.isActive = false;
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
    }
    
    animate() {
        if (!this.isActive) return;
        
        this.animationFrame = requestAnimationFrame(() => this.animate());
        
        // Obtenir les données audio
        if (this.analyser) {
            this.analyser.getByteFrequencyData(this.dataArray);
        }
        
        // Dessiner selon le mode
        this.render();
    }
    
    render() {
        const ctx = this.ctx;
        
        // Clear avec fade effect
        ctx.fillStyle = this.options.colors.background;
        ctx.fillRect(0, 0, this.options.width, this.options.height);
        
        if (!this.dataArray) {
            this.drawIdleState();
            return;
        }
        
        // Dessiner selon le mode
        switch (this.options.mode) {
            case 'spectrum':
                this.drawSpectrum();
                break;
            case 'waveform':
                this.drawWaveform();
                break;
            case 'particles':
                this.drawParticles();
                break;
            default:
                this.drawSpectrum();
        }
        
        // Info overlay
        this.drawInfo();
    }
    
    drawSpectrum() {
        const ctx = this.ctx;
        const barWidth = (this.options.width / this.bufferLength) * 2;
        let x = 0;
        
        for (let i = 0; i < this.bufferLength; i++) {
            const barHeight = (this.dataArray[i] / 255) * (this.options.height * 0.8);
            
            // Gradient de couleur basé sur la fréquence
            const hue = (i / this.bufferLength) * 300 + 280; // De violet à cyan
            const saturation = 70 + (this.dataArray[i] / 255) * 30;
            const lightness = 50 + (this.dataArray[i] / 255) * 40;
            
            ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
            
            // Barre principale
            ctx.fillRect(x, this.options.height - barHeight, barWidth, barHeight);
            
            // Effet miroir
            ctx.fillStyle = `hsla(${hue}, ${saturation}%, ${lightness}%, 0.3)`;
            ctx.fillRect(x, this.options.height - barHeight - 20, barWidth, -barHeight * 0.3);
            
            x += barWidth + 1;
        }
    }
    
    drawWaveform() {\n        const ctx = this.ctx;\n        const centerY = this.center.y;\n        const amplitude = this.options.height * 0.4;\n        \n        // Simuler une forme d'onde basée sur le spectrum\n        ctx.strokeStyle = this.options.colors.primary;\n        ctx.lineWidth = 3;\n        ctx.beginPath();\n        \n        for (let i = 0; i < this.options.width; i += 2) {\n            const dataIndex = Math.floor((i / this.options.width) * this.bufferLength);\n            const value = this.dataArray[dataIndex] || 0;\n            const y = centerY + (value / 255 - 0.5) * amplitude * Math.sin(i * 0.02);\n            \n            if (i === 0) {\n                ctx.moveTo(i, y);\n            } else {\n                ctx.lineTo(i, y);\n            }\n        }\n        \n        ctx.stroke();\n        \n        // Onde secondaire\n        ctx.strokeStyle = this.options.colors.secondary;\n        ctx.lineWidth = 2;\n        ctx.beginPath();\n        \n        for (let i = 0; i < this.options.width; i += 3) {\n            const dataIndex = Math.floor((i / this.options.width) * this.bufferLength);\n            const value = this.dataArray[dataIndex] || 0;\n            const offset = Math.sin(Date.now() * 0.005 + i * 0.01) * 20;\n            const y = centerY + (value / 255 - 0.5) * amplitude * 0.6 + offset;\n            \n            if (i === 0) {\n                ctx.moveTo(i, y);\n            } else {\n                ctx.lineTo(i, y);\n            }\n        }\n        \n        ctx.stroke();\n    }\n    \n    drawParticles() {\n        // Calculer l'énergie audio moyenne\n        let totalEnergy = 0;\n        for (let i = 0; i < this.bufferLength; i++) {\n            totalEnergy += this.dataArray[i];\n        }\n        const avgEnergy = totalEnergy / this.bufferLength / 255;\n        \n        // Mettre à jour et dessiner les particules\n        this.particles.forEach((particle, index) => {\n            const frequencyIndex = Math.floor((index / this.particles.length) * this.bufferLength);\n            const frequency = this.dataArray[frequencyIndex] / 255;\n            \n            particle.update(avgEnergy, frequency);\n            particle.draw(this.ctx, this.options.colors);\n        });\n    }\n    \n    drawIdleState() {\n        const ctx = this.ctx;\n        \n        // Animation d'attente\n        const time = Date.now() * 0.003;\n        const centerX = this.center.x;\n        const centerY = this.center.y;\n        \n        // Cercles pulsants\n        for (let i = 0; i < 3; i++) {\n            const radius = 30 + i * 20 + Math.sin(time + i) * 10;\n            const alpha = 0.3 - i * 0.1;\n            \n            ctx.strokeStyle = `rgba(255, 100, 200, ${alpha})`;\n            ctx.lineWidth = 2;\n            ctx.beginPath();\n            ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);\n            ctx.stroke();\n        }\n        \n        // Texte\n        ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';\n        ctx.font = '16px Arial';\n        ctx.textAlign = 'center';\n        ctx.fillText('En attente d\\'audio...', centerX, centerY + 80);\n    }\n    \n    drawInfo() {\n        const ctx = this.ctx;\n        \n        // Mode actuel\n        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';\n        ctx.font = '12px Arial';\n        ctx.textAlign = 'left';\n        ctx.fillText(`Mode: ${this.options.mode.toUpperCase()}`, 10, 20);\n        \n        // FPS (approximatif)\n        const fps = this.isActive ? '60' : '0';\n        ctx.fillText(`FPS: ${fps}`, 10, 35);\n        \n        // Audio status\n        const audioStatus = this.audioPlayer.isPlaying ? 'PLAYING' : 'PAUSED';\n        ctx.fillStyle = this.audioPlayer.isPlaying ? 'rgba(100, 255, 100, 0.8)' : 'rgba(255, 100, 100, 0.8)';\n        ctx.fillText(audioStatus, 10, 50);\n    }\n    \n    // API publique\n    setMode(mode) {\n        if (['spectrum', 'waveform', 'particles'].includes(mode)) {\n            this.options.mode = mode;\n            console.log(`🎨 Mode visualisation: ${mode}`);\n        }\n    }\n    \n    setColors(colors) {\n        Object.assign(this.options.colors, colors);\n    }\n    \n    resize(width, height) {\n        this.options.width = width;\n        this.options.height = height;\n        this.setupCanvas();\n    }\n    \n    toggle() {\n        if (this.isActive) {\n            this.stopVisualization();\n        } else {\n            this.startVisualization();\n        }\n    }\n}\n\n// Classe particule simple\nclass SimpleParticle {\n    constructor(canvasWidth, canvasHeight) {\n        this.reset(canvasWidth, canvasHeight);\n        this.canvasWidth = canvasWidth;\n        this.canvasHeight = canvasHeight;\n    }\n    \n    reset(canvasWidth, canvasHeight) {\n        this.x = Math.random() * canvasWidth;\n        this.y = Math.random() * canvasHeight;\n        this.vx = (Math.random() - 0.5) * 2;\n        this.vy = (Math.random() - 0.5) * 2;\n        this.size = Math.random() * 4 + 1;\n        this.life = 1;\n        this.decay = 0.005 + Math.random() * 0.005;\n    }\n    \n    update(energy, frequency) {\n        // Mouvement influencé par l'audio\n        const audioInfluence = energy * 3;\n        this.vx += (Math.random() - 0.5) * audioInfluence;\n        this.vy += (Math.random() - 0.5) * audioInfluence;\n        \n        // Limiter la vitesse\n        this.vx = Math.max(-5, Math.min(5, this.vx));\n        this.vy = Math.max(-5, Math.min(5, this.vy));\n        \n        // Déplacement\n        this.x += this.vx;\n        this.y += this.vy;\n        \n        // Rebonds\n        if (this.x <= 0 || this.x >= this.canvasWidth) this.vx *= -0.7;\n        if (this.y <= 0 || this.y >= this.canvasHeight) this.vy *= -0.7;\n        \n        // Contraintes\n        this.x = Math.max(0, Math.min(this.canvasWidth, this.x));\n        this.y = Math.max(0, Math.min(this.canvasHeight, this.y));\n        \n        // Taille audio-réactive\n        this.size = Math.max(1, this.size * 0.98 + frequency * 8);\n        \n        // Vie\n        this.life -= this.decay;\n        if (this.life <= 0) {\n            this.reset(this.canvasWidth, this.canvasHeight);\n        }\n    }\n    \n    draw(ctx, colors) {\n        const alpha = this.life;\n        \n        // Particule principale\n        ctx.fillStyle = `rgba(255, 100, 200, ${alpha})`;\n        ctx.beginPath();\n        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);\n        ctx.fill();\n        \n        // Halo\n        ctx.fillStyle = `rgba(100, 255, 255, ${alpha * 0.3})`;\n        ctx.beginPath();\n        ctx.arc(this.x, this.y, this.size * 2, 0, Math.PI * 2);\n        ctx.fill();\n    }\n}\n\n// Export\nwindow.AudioVisualizer = AudioVisualizer;