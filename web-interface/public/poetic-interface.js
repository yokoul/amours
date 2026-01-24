/* ===========================
   INTERFACE POÉTIQUE - LOGIQUE D'INTERACTION
   Architecture de states artistique
   =========================== */

class PoeticInterface {
    constructor() {
        this.currentState = 'contemplation';
        this.selectedWords = [];
        this.currentAudio = null;
        this.archive = [];
        this.archiveIsOpen = false;
        this.spider = null;  // Visualisation sémantique
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setupGestures();
        this.loadArchive();
        console.log('🎭 Interface poétique initialisée');
    }
    
    /* ===========================
       GESTION DES ÉTATS
       =========================== */
    
    setState(newState) {
        const app = document.getElementById('app');
        const oldState = this.currentState;
        
        console.log(`🔄 Transition: ${oldState} → ${newState}`);
        
        // Transition douce avec timing artistique
        app.style.opacity = '0.9';
        
        setTimeout(() => {
            this.currentState = newState;
            app.setAttribute('data-state', newState);
            
            // Actions spécifiques par état
            this.onStateEnter(newState, oldState);
            
            app.style.opacity = '1';
        }, 300);
    }
    
    onStateEnter(state, previousState) {
        switch(state) {
            case 'contemplation':
                this.resetInterface();
                break;
                
            case 'inspiration':
                this.loadWords();
                break;
                
            case 'creation':
                // L'interface audio est configurée dans setupAudioPlayer
                break;
        }
    }
    
    /* ===========================
       ÉVÉNEMENTS & INTERACTIONS
       =========================== */
    
    bindEvents() {
        // Point d'entrée - Tap pour commencer
        const entryPoint = document.getElementById('entry-point');
        entryPoint.addEventListener('click', () => {
            this.hapticFeedback();
            this.setState('inspiration');
        });
        
        // Support clavier pour le point d'entrée
        entryPoint.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.hapticFeedback();
                this.setState('inspiration');
            }
        });
        
        // Bouton de génération
        const generateBtn = document.getElementById('generate-btn');
        generateBtn.addEventListener('click', () => this.generatePhrases());
        
        // Navigation d'état
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.getAttribute('data-action');
                this.handleNavigation(action);
            });
        });
        
        // Archive
        const archiveBtn = document.querySelector('[data-action="archive"]');
        const closeArchive = document.getElementById('close-archive');
        
        archiveBtn?.addEventListener('click', () => this.openArchive());
        closeArchive?.addEventListener('click', () => this.closeArchive());
    }
    
    setupGestures() {
        // Swipe up pour archive et swipe down pour fermer
        let startY = 0;
        let startX = 0;
        let moveDetected = false;
        
        document.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
            startX = e.touches[0].clientX;
            moveDetected = false;
        }, { passive: true });
        
        document.addEventListener('touchmove', (e) => {
            const currentY = e.touches[0].clientY;
            const currentX = e.touches[0].clientX;
            const deltaY = Math.abs(startY - currentY);
            const deltaX = Math.abs(startX - currentX);
            
            // Détecter un mouvement significatif
            if (deltaY > 30 || deltaX > 30) {
                moveDetected = true;
            }
        }, { passive: true });
        
        document.addEventListener('touchend', (e) => {
            if (!moveDetected) return; // Pas de swipe, laisser les clicks fonctionner
            
            const currentY = e.changedTouches[0].clientY;
            const deltaY = startY - currentY;
            const deltaX = Math.abs(startX - e.changedTouches[0].clientX);
            
            // Swipe up détecté : mouvement vertical important et peu d'horizontal
            if (deltaY > 150 && deltaX < 50 && !this.archiveIsOpen) {
                this.openArchive();
            }
            
            // Swipe down pour fermer l'archive
            if (deltaY < -150 && deltaX < 50 && this.archiveIsOpen) {
                this.closeArchive();
            }
        }, { passive: true });
    }
    
    /* ===========================
       ÉTAT INSPIRATION - Mots
       =========================== */
    
    async loadWords() {
        const wordCloud = document.getElementById('word-cloud');
        wordCloud.innerHTML = '';
        
        // Mots de démonstration (utilisés immédiatement)
        const demoWords = [
            'âme', 'souffle', 'éternité', 'caresse', 
            'murmure', 'regard', 'silence', 'passion',
            'lumière', 'émoi', 'tendresse', 'vertige',
            'abandon', 'frisson', 'mystère', 'ivresse'
        ];
        
        let wordsToDisplay = demoWords;
        
        try {
            // Essayer de charger depuis l'API avec timeout
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 2000);
            
            const response = await fetch('/api/words', { signal: controller.signal });
            clearTimeout(timeout);
            
            if (response.ok) {
                const words = await response.json();
                if (Array.isArray(words) && words.length > 0) {
                    wordsToDisplay = words;
                    console.log('✅ Mots chargés depuis l\'API');
                }
            }
        } catch (error) {
            console.log('ℹ️ Utilisation des mots par défaut:', error.message);
        }
        
        // Apparition progressive des mots
        wordsToDisplay.forEach((word, index) => {
            setTimeout(() => {
                this.createWordElement(word, wordCloud);
            }, index * 80); // Délai artistique
        });
    }
    
    createWordElement(word, container) {
        const wordEl = document.createElement('button');
        wordEl.className = 'word-item';
        wordEl.textContent = word;
        wordEl.style.animationDelay = '0s';
        
        // Tap long pour sélection intentionnelle
        let pressTimer;
        
        wordEl.addEventListener('touchstart', (e) => {
            pressTimer = setTimeout(() => {
                this.selectWord(word, wordEl);
                this.hapticFeedback('selection');
            }, 500); // 500ms pour "intention"
        });
        
        wordEl.addEventListener('touchend', () => {
            clearTimeout(pressTimer);
        });
        
        // Fallback pour desktop
        wordEl.addEventListener('click', () => {
            this.selectWord(word, wordEl);
        });
        
        container.appendChild(wordEl);
    }
    
    selectWord(word, element) {
        if (this.selectedWords.includes(word)) return;
        
        this.selectedWords.push(word);
        element.classList.add('selected');
        
        this.updateSelectedWordsDisplay();
        this.updateGenerateButton();
        
        // Effet visuel de sélection
        element.style.transform = 'scale(0.95)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
    }
    
    updateSelectedWordsDisplay() {
        const container = document.getElementById('selected-words');
        container.innerHTML = '';
        
        this.selectedWords.forEach(word => {
            const wordEl = document.createElement('span');
            wordEl.className = 'selected-word';
            wordEl.textContent = word;
            container.appendChild(wordEl);
        });
    }
    
    updateGenerateButton() {
        const btn = document.getElementById('generate-btn');
        if (this.selectedWords.length >= 2) {
            btn.classList.add('ready');
        } else {
            btn.classList.remove('ready');
        }
    }
    
    /* ===========================
       ÉTAT CRÉATION - Audio
       =========================== */
    
    async generatePhrases() {
        if (this.selectedWords.length < 2) return;
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    words: this.selectedWords,
                    count: this.selectedWords.length // Une phrase par mot sélectionné
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `Erreur serveur: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('📦 Résultat reçu:', result);
            
            if (!result.success) {
                throw new Error(result.error || 'Génération échouée');
            }
            
            // Vérifier que nous avons les données nécessaires
            const audioUrl = result.audio_url || result.audioFile;
            if (!audioUrl) {
                throw new Error('Aucun fichier audio généré');
            }
            
            // Extraire le texte complet des phrases
            let fullPhrase = '';
            if (result.phrases && result.phrases.length > 0) {
                // Concaténer toutes les phrases avec un séparateur
                fullPhrase = result.phrases.map(p => p.text).join(' (...) ');
            } else if (result.phrase) {
                fullPhrase = result.phrase;
            } else {
                fullPhrase = `Création avec ${this.selectedWords.join(', ')}`;
            }
            
            this.currentAudio = audioUrl;
            this.currentPhrase = fullPhrase;
            
            // Transition vers état création
            this.setState('creation');
            this.setupAudioPlayer({
                audioFile: audioUrl,
                phrase: fullPhrase,
                phrases: result.phrases || [],
                duration_seconds: result.duration_seconds,
                semantic_analysis: result.semantic_analysis  // Ajouter l'analyse sémantique
            });
            
            // Sauvegarder dans l'archive
            this.addToArchive({
                words: [...this.selectedWords],
                phrase: fullPhrase,
                audioFile: audioUrl,
                timestamp: result.timestamp || Date.now(),
                phrases: result.phrases || []
            });
            
        } catch (error) {
            console.error('❌ Erreur de génération:', error);
            const errorMsg = error.message || 'Erreur de création';
            this.showError(errorMsg);
            // Revenir à l'état inspiration après une erreur
            setTimeout(() => {
                this.setState('inspiration');
            }, 2000);
        } finally {
            this.hideLoading();
        }
    }
    
    setupAudioPlayer(data) {
        const phraseDisplay = document.getElementById('phrase-display');
        const playBtn = document.getElementById('play-btn');
        const progressBar = document.getElementById('progress-bar');
        
        // Afficher le texte de la phrase
        phraseDisplay.textContent = data.phrase || 'Création poétique';
        phraseDisplay.style.opacity = '1';
        
        // Configuration du lecteur audio
        if (this.audioElement) {
            this.audioElement.pause();
            this.audioElement.remove();
        }
        
        this.audioElement = new Audio(data.audioFile);
        
        // Événements audio
        this.audioElement.addEventListener('loadedmetadata', () => {
            this.generateWaveform();
        });
        
        this.audioElement.addEventListener('timeupdate', () => {
            const progress = (this.audioElement.currentTime / this.audioElement.duration) * 100;
            progressBar.style.width = `${progress}%`;
        });
        
        this.audioElement.addEventListener('ended', () => {
            playBtn.innerHTML = '<span class="play-symbol">▶</span>';
            progressBar.style.width = '0%';
        });
        
        // Contrôle de lecture
        playBtn.onclick = () => this.togglePlayback();
        
        // Visualisation sémantique
        if (data.semantic_analysis) {
            this.showSemanticVisualization(data.semantic_analysis);
        }
    }
    
    showSemanticVisualization(semanticData) {
        console.log('🕷️ showSemanticVisualization appelé avec:', semanticData);
        
        if (!semanticData || Object.keys(semanticData).length === 0) {
            console.warn('⚠️ Pas de données sémantiques à afficher');
            return;
        }
        
        // Créer le spider si nécessaire
        if (!this.spider) {
            console.log('🕷️ Création du spider...');
            this.spider = new SpiderMinimal('spider-container', {
                size: 280,
                categories: Object.keys(semanticData)
            });
        }
        
        // Afficher les données avec animation
        console.log('🕷️ Affichage des données:', semanticData);
        this.spider.setData(semanticData, true);
        
        // Rendre visible avec transition
        const container = document.getElementById('spider-container');
        container.style.opacity = '0';
        container.style.display = 'block';
        
        setTimeout(() => {
            container.style.opacity = '1';
            console.log('✅ Spider affiché');
        }, 300);
    }
    
    togglePlayback() {
        const playBtn = document.getElementById('play-btn');
        
        if (this.audioElement.paused) {
            this.audioElement.play();
            playBtn.innerHTML = '<span class="play-symbol">⏸</span>';
            this.hapticFeedback();
        } else {
            this.audioElement.pause();
            playBtn.innerHTML = '<span class="play-symbol">▶</span>';
        }
    }
    
    generateWaveform() {
        const waveform = document.getElementById('waveform');
        waveform.innerHTML = '';
        
        // Créer des barres fixes qui s'animeront pendant la lecture
        this.waveBars = [];
        const numBars = 50;
        
        for (let i = 0; i < numBars; i++) {
            const bar = document.createElement('div');
            bar.className = 'wave-bar';
            const baseHeight = 20 + Math.sin(i / 5) * 30 + Math.random() * 30;
            bar.style.height = `${baseHeight}%`;
            bar.setAttribute('data-base-height', baseHeight);
            waveform.appendChild(bar);
            this.waveBars.push(bar);
        }
        
        // Animer pendant la lecture
        if (this.audioElement) {
            this.audioElement.addEventListener('timeupdate', () => {
                if (!this.audioElement.paused) {
                    this.animateWaveform();
                }
            });
        }
    }
    
    animateWaveform() {
        if (!this.waveBars) return;
        
        const progress = this.audioElement.currentTime / this.audioElement.duration;
        const currentBar = Math.floor(progress * this.waveBars.length);
        
        this.waveBars.forEach((bar, i) => {
            if (i === currentBar) {
                bar.classList.add('active');
            } else {
                bar.classList.remove('active');
            }
        });
    }
    
    /* ===========================
       ARCHIVE & MÉMOIRE
       =========================== */
    
    addToArchive(item) {
        this.archive.unshift(item); // Plus récent en premier
        this.saveArchive();
        this.updateArchiveDisplay();
    }
    
    openArchive() {
        const archive = document.getElementById('archive');
        archive.classList.add('open');
        this.updateArchiveDisplay();
        this.archiveIsOpen = true;
    }
    
    closeArchive() {
        const archive = document.getElementById('archive');
        archive.classList.remove('open');
        this.archiveIsOpen = false;
    }
    
    updateArchiveDisplay() {
        const container = document.getElementById('archive-list');
        container.innerHTML = '';
        
        if (this.archive.length === 0) {
            container.innerHTML = '<p style="text-align: center; opacity: 0.5; margin-top: 2rem;">aucune création</p>';
            return;
        }
        
        this.archive.forEach((item, index) => {
            const itemEl = document.createElement('div');
            itemEl.className = 'archive-item';
            
            const date = new Date(item.timestamp).toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            itemEl.innerHTML = `
                <div class="archive-meta">${date} • ${item.words.join(' + ')}</div>
                <div class="archive-phrase">${item.phrase}</div>
            `;
            
            itemEl.addEventListener('click', () => {
                this.playFromArchive(item);
                this.closeArchive();
            });
            
            container.appendChild(itemEl);
        });
    }
    
    playFromArchive(item) {
        this.currentAudio = item.audioFile;
        this.currentPhrase = item.phrase;
        this.setState('creation');
        this.setupAudioPlayer(item);
    }
    
    /* ===========================
       NAVIGATION & UTILITAIRES
       =========================== */
    
    handleNavigation(action) {
        switch(action) {
            case 'restart':
                this.setState('contemplation');
                break;
                
            case 'archive':
                this.openArchive();
                break;
        }
    }
    
    resetInterface() {
        this.selectedWords = [];
        this.currentAudio = null;
        this.currentPhrase = null;
        
        if (this.audioElement) {
            this.audioElement.pause();
            this.audioElement = null;
        }
        
        // Reset des displays
        document.getElementById('selected-words').innerHTML = '';
        document.getElementById('phrase-display').innerHTML = '';
        document.getElementById('word-cloud').innerHTML = '';
    }
    
    /* ===========================
       FEEDBACK & ANIMATIONS
       =========================== */
    
    hapticFeedback(type = 'light') {
        if ('vibrate' in navigator) {
            switch(type) {
                case 'light':
                    navigator.vibrate(10);
                    break;
                case 'selection':
                    navigator.vibrate([10, 50, 10]);
                    break;
                case 'success':
                    navigator.vibrate([50, 100, 50]);
                    break;
            }
        }
    }
    
    showLoading() {
        // Implémentation d'un loading subtil
        document.body.style.cursor = 'wait';
        let loader = document.getElementById('loading-indicator');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'loading-indicator';
            loader.className = 'loading';
            document.body.appendChild(loader);
        }
        loader.classList.add('show');
    }
    
    hideLoading() {
        document.body.style.cursor = 'default';
        const loader = document.getElementById('loading-indicator');
        if (loader) {
            loader.classList.remove('show');
        }
    }
    
    showError(message) {
        // Notification d'erreur minimale
        const errorMsg = typeof message === 'string' ? message : message.message || 'Erreur inconnue';
        console.error('❌ Erreur:', errorMsg);
        
        // Afficher brièvement à l'utilisateur
        const phraseDisplay = document.getElementById('phrase-display');
        if (phraseDisplay && this.currentState === 'creation') {
            phraseDisplay.textContent = errorMsg;
            phraseDisplay.style.opacity = '0.6';
        }
    }
    
    /* ===========================
       PERSISTANCE LOCALE
       =========================== */
    
    saveArchive() {
        try {
            localStorage.setItem('poetic-archive', JSON.stringify(this.archive));
        } catch (e) {
            console.warn('Impossible de sauvegarder l\'archive:', e);
        }
    }
    
    loadArchive() {
        try {
            const saved = localStorage.getItem('poetic-archive');
            if (saved) {
                this.archive = JSON.parse(saved);
            }
        } catch (e) {
            console.warn('Impossible de charger l\'archive:', e);
            this.archive = [];
        }
    }
}

/* ===========================
   VISUALISATION SÉMANTIQUE
   =========================== */

class SemanticVisualization {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.isAnimating = false;
        
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }
    
    resizeCanvas() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * window.devicePixelRatio;
        this.canvas.height = rect.height * window.devicePixelRatio;
        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
    
    start(words) {
        this.particles = words.map((word, i) => ({
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            word: word,
            connections: []
        }));
        
        this.isAnimating = true;
        this.animate();
    }
    
    animate() {
        if (!this.isAnimating) return;
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Mise à jour et rendu des particules
        this.particles.forEach(particle => {
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // Rebond sur les bords
            if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;
            
            // Rendu minimaliste
            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, 2, 0, Math.PI * 2);
            this.ctx.fill();
        });
        
        requestAnimationFrame(() => this.animate());
    }
    
    stop() {
        this.isAnimating = false;
    }
}

/* ===========================
   INITIALISATION
   =========================== */

document.addEventListener('DOMContentLoaded', () => {
    // Interface principale
    window.poeticInterface = new PoeticInterface();
    
    // Visualisation sémantique
    const canvas = document.getElementById('semantic-canvas');
    if (canvas) {
        window.semanticViz = new SemanticVisualization(canvas);
    }
    
    console.log('🎭 Interface poétique prête');
});