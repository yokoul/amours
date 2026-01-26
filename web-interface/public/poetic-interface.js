/* ===========================
   INTERFACE POÉTIQUE - LOGIQUE D'INTERACTION
   Architecture de states artistique
   =========================== */

/* ===========================
   SPIDER MINIMAL - VISUALISATION SÉMANTIQUE
   =========================== */
class SpiderMinimal {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error(`❌ Canvas #${canvasId} non trouvé`);
            return;
        }
        
        this.ctx = this.canvas.getContext('2d');
        this.data = null;
        this.animatedData = {};
        this.isAnimating = false;
        
        this.options = {
            size: options.size || 280,
            categories: options.categories || [
                'romantique', 'passionnel', 'tendre', 'physique',
                'platonique', 'familial', 'amical', 'spirituel'
            ],
            colors: {
                background: 'transparent',
                grid: 'rgba(0, 0, 0, 0.1)',
                data: 'rgba(0, 0, 0, 0.15)',
                stroke: 'rgba(0, 0, 0, 0.8)',
                text: 'rgba(0, 0, 0, 0.7)',
                points: 'rgba(0, 0, 0, 1)'
            },
            ...options
        };
        
        this.setupCanvas();
        console.log('🕷️ Spider minimal initialisé');
    }
    
    setupCanvas() {
        const size = this.options.size;
        this.canvas.width = size;
        this.canvas.height = size;
        this.canvas.style.width = `${size}px`;
        this.canvas.style.height = `${size}px`;
        
        this.center = { x: size / 2, y: size / 2 };
        this.radius = size * 0.32;
    }
    
    setData(newData, animate = true) {
        if (!newData) return;
        this.data = this.normalizeData(newData);
        if (animate && !this.isAnimating) {
            this.animateToNewData();
        } else {
            this.animatedData = {...this.data};
            this.render();
        }
    }
    
    normalizeData(data) {
        const normalized = {};
        this.options.categories.forEach(cat => {
            normalized[cat] = data[cat] || 0;
        });
        return normalized;
    }
    
    animateToNewData() {
        this.isAnimating = true;
        const duration = 800;
        const startTime = Date.now();
        const startData = {...this.animatedData};
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2;
            
            this.options.categories.forEach(cat => {
                const start = startData[cat] || 0;
                const end = this.data[cat] || 0;
                this.animatedData[cat] = start + (end - start) * eased;
            });
            
            this.render();
            if (progress < 1) requestAnimationFrame(animate);
            else this.isAnimating = false;
        };
        animate();
    }
    
    render() {
        const ctx = this.ctx;
        const {center, radius} = this;
        
        ctx.clearRect(0, 0, this.options.size, this.options.size);
        
        // Grille
        ctx.strokeStyle = this.options.colors.grid;
        ctx.lineWidth = 1;
        for (let i = 1; i <= 4; i++) {
            ctx.beginPath();
            ctx.arc(center.x, center.y, (radius * i) / 4, 0, Math.PI * 2);
            ctx.stroke();
        }
        
        // Axes
        const categories = this.options.categories;
        const angleStep = (Math.PI * 2) / categories.length;
        for (let i = 0; i < categories.length; i++) {
            const angle = i * angleStep - Math.PI / 2;
            ctx.beginPath();
            ctx.moveTo(center.x, center.y);
            ctx.lineTo(center.x + Math.cos(angle) * radius, center.y + Math.sin(angle) * radius);
            ctx.stroke();
        }
        
        // Données
        if (this.animatedData && Object.keys(this.animatedData).length > 0) {
            ctx.fillStyle = this.options.colors.data;
            ctx.strokeStyle = this.options.colors.stroke;
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            for (let i = 0; i < categories.length; i++) {
                const angle = i * angleStep - Math.PI / 2;
                const value = this.animatedData[categories[i]] || 0;
                const distance = radius * value;
                const x = center.x + Math.cos(angle) * distance;
                const y = center.y + Math.sin(angle) * distance;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            
            ctx.closePath();
            ctx.fill();
            ctx.stroke();
            
            // Points
            ctx.fillStyle = this.options.colors.points;
            for (let i = 0; i < categories.length; i++) {
                const angle = i * angleStep - Math.PI / 2;
                const value = this.animatedData[categories[i]] || 0;
                const distance = radius * value;
                const x = center.x + Math.cos(angle) * distance;
                const y = center.y + Math.sin(angle) * distance;
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        
        // Labels
        ctx.fillStyle = this.options.colors.text;
        ctx.font = '10px -apple-system, BlinkMacSystemFont, sans-serif';
        for (let i = 0; i < categories.length; i++) {
            const angle = i * angleStep - Math.PI / 2;
            const x = center.x + Math.cos(angle) * (radius + 20);
            const y = center.y + Math.sin(angle) * (radius + 20);
            ctx.textAlign = Math.cos(angle) < -0.1 ? 'right' : Math.cos(angle) > 0.1 ? 'left' : 'center';
            ctx.fillText(categories[i], x, y + 4);
        }
    }
}

/* ===========================
   INTERFACE PRINCIPALE
   =========================== */
class PoeticInterface {
    constructor() {
        this.currentState = 'contemplation';
        this.selectedWords = [];
        this.includeNextMode = 0; // Mode de longueur: 0=court, 1=moyen, 2=long
        this.currentAudio = null;
        this.archive = [];
        this.archiveIsOpen = false;
        this.spider = null;  // Visualisation sémantique
        this.segments = null;  // Timeline des segments audio
        this.totalDuration = 0;
        this.karaokeData = null;  // Données pour le karaoké mot par mot
        this.currentPhraseIndex = 0;
        this.karaokeEnabled = true;  // Karaoké activé par défaut
        
        this.init();
    }
    
    init() {
        this.loadTheme();
        this.loadKaraokePreference();
        this.bindEvents();
        this.setupGestures();
        this.loadArchive();
        this.updateGenerateButton();
        console.log('🎭 Interface poétique initialisée');
    }
    
    /* ===========================
       GESTION DU THÈME
       =========================== */
    
    loadTheme() {
        // Charger le thème depuis localStorage
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.setAttribute('data-theme', 'dark');
        }
    }
    
    toggleTheme() {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        if (newTheme === 'dark') {
            document.body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        }
        
        console.log(`🎨 Thème changé: ${newTheme}`);
    }
    
    /* ===========================
       GESTION DU KARAOKÉ
       =========================== */
    
    loadKaraokePreference() {
        // Charger la préférence karaoké depuis localStorage
        const savedKaraoke = localStorage.getItem('karaokeEnabled');
        this.karaokeEnabled = savedKaraoke !== 'false'; // Activé par défaut
        this.updateKaraokeButton();
    }
    
    toggleKaraoke() {
        this.karaokeEnabled = !this.karaokeEnabled;
        localStorage.setItem('karaokeEnabled', this.karaokeEnabled.toString());
        this.updateKaraokeButton();
        console.log(`🎤 Karaoké ${this.karaokeEnabled ? 'activé' : 'désactivé'}`);
    }
    
    updateKaraokeButton() {
        const btn = document.getElementById('karaoke-toggle-btn');
        if (btn) {
            btn.style.opacity = this.karaokeEnabled ? '1' : '0.5';
            btn.setAttribute('aria-label', this.karaokeEnabled ? 'Désactiver le karaoké' : 'Activer le karaoké');
        }
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
        generateBtn.addEventListener('click', () => this.handleGenerateClick());
        
        // Boutons de contrôle de longueur
        document.querySelectorAll('.length-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const mode = parseInt(e.target.getAttribute('data-mode'));
                this.setIncludeNextMode(mode);
            });
        });
        
        // Bouton de changement de thème
        const themeToggle = document.getElementById('theme-toggle');
        themeToggle?.addEventListener('click', () => {
            this.hapticFeedback();
            this.toggleTheme();
        });
        
        // Navigation d'état
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.getAttribute('data-action');
                this.handleNavigation(action);
            });
        });
        
        // Bouton toggle thème
        const themeToggleBtn = document.getElementById('theme-toggle-btn');
        themeToggleBtn?.addEventListener('click', () => this.toggleTheme());
        
        // Bouton toggle karaoké
        const karaokeToggleBtn = document.getElementById('karaoke-toggle-btn');
        karaokeToggleBtn?.addEventListener('click', () => this.toggleKaraoke());
        
        // Archive
        const archiveBtn = document.querySelector('[data-action="archive"]');
        const closeArchive = document.getElementById('close-archive');
        
        archiveBtn?.addEventListener('click', () => this.openArchive());
        closeArchive?.addEventListener('click', () => this.closeArchive());
        
        // Fermer le tooltip timeline si on clique ailleurs
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.timeline-point')) {
                this.hideTimelineTooltip();
            }
        });
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
            
            // Permettre de retirer en cliquant/touchant
            wordEl.addEventListener('click', (e) => {
                e.stopPropagation();
                this.unselectWord(word);
            });
            
            container.appendChild(wordEl);
        });
    }
    
    unselectWord(word) {
        // Retirer le mot de la liste
        const index = this.selectedWords.indexOf(word);
        if (index > -1) {
            this.selectedWords.splice(index, 1);
        }
        
        // Retirer la classe 'selected' du mot dans le nuage
        const wordElements = document.querySelectorAll('.word-item');
        wordElements.forEach(el => {
            if (el.textContent === word) {
                el.classList.remove('selected');
            }
        });
        
        // Mettre à jour l'affichage
        this.updateSelectedWordsDisplay();
        this.updateGenerateButton();
    }
    
    setIncludeNextMode(mode) {
        this.includeNextMode = mode;
        
        // Mettre à jour les boutons visuellement
        document.querySelectorAll('.length-btn').forEach(btn => {
            const btnMode = parseInt(btn.getAttribute('data-mode'));
            if (btnMode === mode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        console.log(`📏 Mode de longueur: ${mode === 0 ? 'court' : mode === 1 ? 'moyen (+1)' : 'long (+2)'}`);
    }
    
    updateGenerateButton() {
        const btn = document.getElementById('generate-btn');
        const label = btn.querySelector('span');
        if (this.selectedWords.length >= 2) {
            btn.classList.add('ready');
            btn.classList.remove('shake-mode');
            if (label) label.textContent = 'créer';
        } else {
            btn.classList.remove('ready');
            btn.classList.add('shake-mode');
            if (label) label.textContent = 'autres mots';
        }
    }

    handleGenerateClick() {
        if (this.selectedWords.length < 2) {
            this.refreshWordList();
            return;
        }

        this.generatePhrases();
    }

    async refreshWordList() {
        const btn = document.getElementById('generate-btn');
        btn.classList.add('shake');
        setTimeout(() => btn.classList.remove('shake'), 400);

        this.selectedWords = [];
        this.updateSelectedWordsDisplay();
        this.updateGenerateButton();

        await this.loadWords();
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
                    count: this.selectedWords.length, // Une phrase par mot sélectionné
                    includeNext: this.includeNextMode // 0, 1 ou 2 phrases suivantes
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
            
            // Attendre que setState finisse son animation (300ms) avant de setup l'audio
            setTimeout(() => {
                this.setupAudioPlayer({
                    audioFile: audioUrl,
                    phrase: fullPhrase,
                    phrases: result.phrases || [],
                    duration_seconds: result.duration_seconds,
                    semantic_analysis: result.semantic_analysis
                });
            }, 350); // Un peu plus que les 300ms de setState
            
            // Sauvegarder dans l'archive
            this.addToArchive({
                words: [...this.selectedWords],
                phrase: fullPhrase,
                audioFile: audioUrl,
                duration: result.duration_seconds || 0,
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
        
        // Stocker les données pour le karaoké
        this.karaokeData = data.phrases || [];
        this.currentPhraseIndex = 0;
        
        // Afficher le texte initial avec structure pour karaoké
        this.renderKaraokeText();
        phraseDisplay.style.opacity = '1';
        
        // Configuration du lecteur audio
        if (this.audioElement) {
            this.audioElement.pause();
            this.audioElement.remove();
        }
        
        this.audioElement = new Audio(data.audioFile);
        
        // Générer la timeline des segments si on a les données de phrases
        if (data.phrases && data.phrases.length > 0) {
            this.generateSegmentTimeline(data.phrases);
        }
        
        // Événements audio
        this.audioElement.addEventListener('loadedmetadata', () => {
            // Timeline déjà générée avec les données réelles
        });
        
        this.audioElement.addEventListener('timeupdate', () => {
            // Animer la timeline des segments et le karaoké
            if (this.audioElement && !this.audioElement.paused) {
                this.animateSegmentTimeline();
                this.animateKaraoke();
            }
        });
        
        this.audioElement.addEventListener('ended', () => {
            playBtn.innerHTML = '<span class="play-symbol">▶</span>';
            // Réinitialiser la timeline
            if (this.segments) {
                this.segments.forEach(seg => seg.element.classList.remove('active', 'played'));
            }
            if (this.timelineCursor) {
                this.timelineCursor.style.left = '0%';
            }
        });
        
        // Contrôle de lecture
        playBtn.onclick = () => this.togglePlayback();
        
        // Afficher la timeline sémantique pour chaque phrase
        if (data.phrases && data.phrases.length > 0) {
            this.showSemanticTimeline(data.phrases);
        }
    }
    
    showSemanticTimeline(phrases) {
        console.log('📈 Affichage timeline sémantique pour', phrases.length, 'phrases');
        
        // Créer ou récupérer le conteneur
        let container = document.getElementById('semantic-timeline');
        if (!container) {
            const audioPlayer = document.getElementById('audio-player');
            container = document.createElement('div');
            container.id = 'semantic-timeline';
            container.className = 'semantic-timeline';
            audioPlayer.appendChild(container);
        }
        
        container.innerHTML = ''; // Clear
        
        // Ligne horizontale principale
        const timeline = document.createElement('div');
        timeline.className = 'timeline-track';
        
        // Pour chaque phrase, créer un point sur la timeline
        phrases.forEach((phrase, index) => {
            if (!phrase.love_analysis) return;
            
            // Trouver le type d'amour dominant
            const dominantType = Object.entries(phrase.love_analysis)
                .sort((a, b) => b[1] - a[1])[0];
            
            // Créer le point de la phrase
            const point = document.createElement('div');
            point.className = 'timeline-point';
            point.setAttribute('data-phrase-index', index);
            
            // Numéro de la phrase
            const number = document.createElement('div');
            number.className = 'point-number';
            number.textContent = index + 1;
            point.appendChild(number);
            
            // Indicateur du type dominant (code couleur ou lettre)
            const indicator = document.createElement('div');
            indicator.className = 'point-indicator';
            indicator.textContent = dominantType[0].substring(0, 3).toUpperCase();
            indicator.title = `${dominantType[0]}: ${(dominantType[1] * 100).toFixed(0)}%`;
            indicator.style.opacity = 0.3 + (dominantType[1] * 0.7); // Intensité
            point.appendChild(indicator);
            
            // Détection tactile vs souris
            const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
            let tooltipVisible = false;
            
            if (!isTouchDevice) {
                // Desktop: hover
                point.addEventListener('mouseenter', () => {
                    this.showTimelineTooltip(point, phrase, index);
                    tooltipVisible = true;
                });
                
                point.addEventListener('mouseleave', () => {
                    this.hideTimelineTooltip();
                    tooltipVisible = false;
                });
            }
            
            // Mobile et Desktop: click pour toggle
            point.addEventListener('click', (e) => {
                e.stopPropagation();
                if (tooltipVisible) {
                    this.hideTimelineTooltip();
                    tooltipVisible = false;
                } else {
                    this.showTimelineTooltip(point, phrase, index);
                    tooltipVisible = true;
                }
            });
            
            timeline.appendChild(point);
        });
        
        container.appendChild(timeline);
        container.style.display = 'block';
        console.log('✅ Timeline affichée');
    }
    
    showTimelineTooltip(pointElement, phrase, index) {
        // Créer ou récupérer le tooltip
        let tooltip = document.getElementById('timeline-tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'timeline-tooltip';
            tooltip.className = 'timeline-tooltip';
            document.body.appendChild(tooltip);
        }
        
        // Contenu du tooltip
        let content = `<div class="tooltip-phrase">${index + 1}. ${phrase.text.substring(0, 60)}...</div>`;
        content += '<div class="tooltip-values">';
        
        Object.entries(phrase.love_analysis)
            .sort((a, b) => b[1] - a[1])
            .forEach(([type, value]) => {
                const percentage = (value * 100).toFixed(0);
                content += `<div class="tooltip-row"><span>${type}</span><span>${percentage}%</span></div>`;
            });
        
        content += '</div>';
        tooltip.innerHTML = content;
        
        // Positionner le tooltip
        const rect = pointElement.getBoundingClientRect();
        tooltip.style.left = `${rect.left + rect.width / 2}px`;
        tooltip.style.top = `${rect.top - 10}px`;
        tooltip.style.display = 'block';
    }
    
    hideTimelineTooltip() {
        const tooltip = document.getElementById('timeline-tooltip');
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    }
    
    showSemanticVisualization(semanticData) {
        console.log('🕷️ showSemanticVisualization appelé avec:', semanticData);
        
        if (!semanticData || Object.keys(semanticData).length === 0) {
            console.warn('⚠️ Pas de données sémantiques à afficher');
            return;
        }
        
        // Créer ou récupérer le spider
        const canvas = document.getElementById('semantic-canvas');
        if (!canvas) {
            console.error('❌ semantic-canvas introuvable');
            return;
        }
        
        if (!this.spider) {
            console.log('🕷️ Création du spider...');
            this.spider = new SpiderMinimal('semantic-canvas', {
                size: 280,
                categories: Object.keys(semanticData)
            });
        }
        
        // Afficher les données
        console.log('🕷️ Mise à jour du spider avec:', semanticData);
        this.spider.setData(semanticData, true);
        
        // Rendre visible
        canvas.style.display = 'block';
        canvas.style.opacity = '1';
        
        console.log('✅ Spider affiché');
    }
    
    togglePlayback() {
        const playBtn = document.getElementById('play-btn');
        
        if (this.audioElement.paused) {
            this.audioElement.play();
            playBtn.innerHTML = '<span class="play-symbol">❙❙</span>';
            this.hapticFeedback();
        } else {
            this.audioElement.pause();
            playBtn.innerHTML = '<span class="play-symbol">▶</span>';
        }
    }
    
    generateSegmentTimeline(phrases) {
        const waveform = document.getElementById('waveform');
        waveform.innerHTML = '';
        
        if (!phrases || phrases.length === 0) return;
        
        // Calculer la durée totale (segments + gaps)
        const totalDuration = phrases.reduce((sum, p) => {
            return sum + (p.real_duration || p.duration) + (p.gap_after || 0);
        }, 0);
        
        this.segments = [];
        let currentTime = 0;
        
        // Créer le conteneur de la timeline avec le curseur
        const timelineContainer = document.createElement('div');
        timelineContainer.className = 'timeline-container';
        
        const timelineTrack = document.createElement('div');
        timelineTrack.className = 'timeline-track';
        
        phrases.forEach((phrase, index) => {
            const duration = phrase.real_duration || phrase.duration;
            const segment = document.createElement('div');
            segment.className = 'timeline-segment';
            
            // Largeur proportionnelle à la durée
            const widthPercent = (duration / totalDuration) * 100;
            segment.style.width = `${widthPercent}%`;
            segment.setAttribute('data-duration', duration.toFixed(1));
            segment.setAttribute('data-start', currentTime.toFixed(1));
            segment.setAttribute('data-end', (currentTime + duration).toFixed(1));
            segment.setAttribute('data-index', index);
            
            // Ajouter un label avec le numéro et la durée
            const label = document.createElement('div');
            label.className = 'segment-label';
            label.textContent = `${index + 1} · ${duration.toFixed(1)}s`;
            segment.appendChild(label);
            
            timelineTrack.appendChild(segment);
            this.segments.push({
                element: segment,
                start: currentTime,
                end: currentTime + duration,
                duration: duration
            });
            
            currentTime += duration;
            
            // Ajouter un gap visuel sauf pour le dernier segment
            if (phrase.gap_after && phrase.gap_after > 0) {
                const gap = document.createElement('div');
                gap.className = 'timeline-gap';
                const gapPercent = (phrase.gap_after / totalDuration) * 100;
                gap.style.width = `${gapPercent}%`;
                timelineTrack.appendChild(gap);
                
                currentTime += phrase.gap_after;
            }
        });
        
        // Ajouter le curseur de progression
        const cursor = document.createElement('div');
        cursor.className = 'timeline-cursor';
        cursor.id = 'timeline-cursor';
        timelineContainer.appendChild(timelineTrack);
        timelineContainer.appendChild(cursor);
        
        waveform.appendChild(timelineContainer);
        
        this.totalDuration = totalDuration;
        this.timelineCursor = cursor;
    }
    
    renderKaraokeText() {
        const phraseDisplay = document.getElementById('phrase-display');
        phraseDisplay.innerHTML = '';
        
        if (!this.karaokeData || this.karaokeData.length === 0) {
            phraseDisplay.textContent = 'Création poétique';
            return;
        }
        
        // Créer un conteneur pour chaque phrase
        this.karaokeData.forEach((phrase, phraseIndex) => {
            if (!phrase.words || phrase.words.length === 0) {
                // Pas de données word-level, afficher le texte brut
                const phraseSpan = document.createElement('span');
                phraseSpan.className = 'phrase-text';
                phraseSpan.textContent = phrase.text;
                phraseDisplay.appendChild(phraseSpan);
                
                if (phraseIndex < this.karaokeData.length - 1) {
                    const separator = document.createElement('span');
                    separator.className = 'phrase-separator';
                    separator.textContent = ' (...) ';
                    phraseDisplay.appendChild(separator);
                }
            } else {
                // Créer un span pour chaque mot avec timestamp
                phrase.words.forEach((wordObj, wordIndex) => {
                    const wordSpan = document.createElement('span');
                    wordSpan.className = 'karaoke-word';
                    wordSpan.textContent = wordObj.word;
                    wordSpan.setAttribute('data-phrase', phraseIndex);
                    wordSpan.setAttribute('data-word', wordIndex);
                    wordSpan.setAttribute('data-start', wordObj.start);
                    wordSpan.setAttribute('data-end', wordObj.end);
                    phraseDisplay.appendChild(wordSpan);
                });
                
                // Séparateur entre phrases
                if (phraseIndex < this.karaokeData.length - 1) {
                    const separator = document.createElement('span');
                    separator.className = 'phrase-separator';
                    separator.textContent = ' (...) ';
                    phraseDisplay.appendChild(separator);
                }
            }
        });
    }
    
    animateKaraoke() {
        // Ne pas animer si le karaoké est désactivé
        if (!this.karaokeEnabled || !this.audioElement || !this.karaokeData) return;
        
        const currentTime = this.audioElement.currentTime;
        const words = document.querySelectorAll('.karaoke-word');
        
        if (words.length === 0) return;
        
        words.forEach(word => {
            const start = parseFloat(word.getAttribute('data-start'));
            const end = parseFloat(word.getAttribute('data-end'));
            
            if (currentTime >= start && currentTime <= end) {
                word.classList.add('active');
            } else {
                word.classList.remove('active');
            }
        });
    }
    
    animateSegmentTimeline() {
        if (!this.segments || !this.audioElement) return;
        
        const currentTime = this.audioElement.currentTime;
        const totalDuration = this.audioElement.duration;
        
        // Déplacer le curseur
        if (this.timelineCursor && totalDuration > 0) {
            const progressPercent = (currentTime / totalDuration) * 100;
            this.timelineCursor.style.left = `${progressPercent}%`;
        }
        
        // Mettre à jour les états des segments
        this.segments.forEach((segment) => {
            if (currentTime >= segment.start && currentTime <= segment.end) {
                segment.element.classList.add('active');
                segment.element.classList.remove('played');
            } else if (currentTime > segment.end) {
                segment.element.classList.add('played');
                segment.element.classList.remove('active');
            } else {
                segment.element.classList.remove('active', 'played');
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
            
            itemEl.innerHTML = `
                <div class="archive-meta">${item.words.join(' + ')}</div>
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
                
            case 'record':
                this.openRecordingInterface();
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
    
    openRecordingInterface() {
        this.hapticFeedback('medium');
        
        // Initialiser l'interface d'enregistrement si pas déjà fait
        if (!window.recordingInterface) {
            window.recordingInterface = new RecordingInterface();
        }
        
        window.recordingInterface.open();
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
        // Overlay grisé
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.className = 'loading-overlay';
            document.body.appendChild(overlay);
        }
        overlay.classList.add('show');
        
        // Spinner
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
        
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.remove('show');
        }
        
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
    // Debug: vérifier que tous les éléments existent
    console.log('🔍 Vérification du DOM:');
    console.log('  - spider-canvas:', document.getElementById('spider-canvas'));
    console.log('  - audio-player:', document.getElementById('audio-player'));
    console.log('  - word-cloud:', document.getElementById('word-cloud'));
    
    // Interface principale
    window.poeticInterface = new PoeticInterface();
    
    // Visualisation sémantique
    const canvas = document.getElementById('semantic-canvas');
    if (canvas) {
        window.semanticViz = new SemanticVisualization(canvas);
    }
    
    console.log('🎭 Interface poétique prête');
});