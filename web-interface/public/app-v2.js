// Application principale v2 - Orchestration des composants
class AudioApp {
    constructor() {
        this.selectedWords = new Set();
        this.audioPlayer = null;
        this.spiderSemantic = null;
        this.audioVisualizer = null;
        this.socket = null;
        
        this.init();
    }
    
    init() {
        console.log('🚀 Initialisation AudioApp v2');
        
        this.setupWebSocket();
        this.initializeComponents();
        this.setupEventListeners();
        this.updateUI();
    }
    
    setupWebSocket() {
        try {
            this.socket = new WebSocket('ws://localhost:3000');
            
            this.socket.onopen = () => {
                console.log('✅ WebSocket connecté');
                this.updateStatus('connection', 'Connecté', true);
            };
            
            this.socket.onclose = () => {
                console.log('❌ WebSocket déconnecté');
                this.updateStatus('connection', 'Déconnecté', false);
            };
            
            this.socket.onerror = (error) => {
                console.error('❌ Erreur WebSocket:', error);
                this.updateStatus('connection', 'Erreur', false);
            };
            
            this.socket.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };
            
        } catch (error) {
            console.log('⚠️ WebSocket non disponible, mode standalone');
            this.updateStatus('connection', 'Mode standalone', false);
        }
    }
    
    initializeComponents() {
        // Initialiser le player audio
        this.audioPlayer = new SimpleAudioPlayer('audio-player-container');
        
        // Initialiser le spider sémantique
        this.spiderSemantic = new SpiderSemantic('spider-semantic');
        
        // Initialiser le visualisateur audio
        this.audioVisualizer = new AudioVisualizer('audio-visualizer', this.audioPlayer);
        
        // Connecter les composants
        this.connectComponents();
    }
    
    connectComponents() {\n        // Écouter les changements de track pour mettre à jour le spider\n        const originalSelectTrack = this.audioPlayer.selectTrack.bind(this.audioPlayer);\n        this.audioPlayer.selectTrack = (index) => {\n            originalSelectTrack(index);\n            \n            // Mettre à jour le spider avec le nouveau track\n            const currentTrack = this.audioPlayer.getCurrentTrack();\n            if (currentTrack) {\n                this.spiderSemantic.updateFromTrack(currentTrack);\n            }\n        };\n        \n        // Écouter les changements de lecture pour le visualisateur\n        const originalOnPlay = this.audioPlayer.onPlay.bind(this.audioPlayer);\n        const originalOnPause = this.audioPlayer.onPause.bind(this.audioPlayer);\n        \n        this.audioPlayer.onPlay = () => {\n            originalOnPlay();\n            this.audioVisualizer.startVisualization();\n        };\n        \n        this.audioPlayer.onPause = () => {\n            originalOnPause();\n            this.audioVisualizer.stopVisualization();\n        };\n    }\n    \n    setupEventListeners() {\n        // Sélection des mots\n        document.querySelectorAll('.word-tile').forEach(tile => {\n            tile.addEventListener('click', () => this.toggleWordSelection(tile));\n        });\n        \n        // Boutons de contrôle\n        document.getElementById('clear-selection').addEventListener('click', () => this.clearSelection());\n        document.getElementById('generate-phrase').addEventListener('click', () => this.generatePhrase());\n        \n        // Contrôles de visualisation\n        document.querySelectorAll('.viz-mode-btn').forEach(btn => {\n            btn.addEventListener('click', () => this.setVisualizationMode(btn.dataset.mode));\n        });\n    }\n    \n    toggleWordSelection(tile) {\n        const word = tile.dataset.word;\n        \n        if (this.selectedWords.has(word)) {\n            this.selectedWords.delete(word);\n            tile.classList.remove('selected');\n        } else {\n            this.selectedWords.add(word);\n            tile.classList.add('selected');\n        }\n        \n        this.updateUI();\n    }\n    \n    clearSelection() {\n        this.selectedWords.clear();\n        document.querySelectorAll('.word-tile').forEach(tile => {\n            tile.classList.remove('selected');\n        });\n        this.updateUI();\n    }\n    \n    generatePhrase() {\n        if (this.selectedWords.size === 0) {\n            this.showNotification('Veuillez sélectionner au moins un mot', 'warning');\n            return;\n        }\n        \n        const wordsArray = Array.from(this.selectedWords);\n        console.log('🎭 Génération avec mots:', wordsArray);\n        \n        this.updateStatus('generation', 'Génération en cours...', 'loading');\n        \n        if (this.socket && this.socket.readyState === WebSocket.OPEN) {\n            // Envoyer via WebSocket\n            this.socket.send(JSON.stringify({\n                type: 'generate_phrases',\n                words: wordsArray,\n                count: 5\n            }));\n        } else {\n            // Simulation pour mode standalone\n            this.simulateGeneration(wordsArray);\n        }\n    }\n    \n    simulateGeneration(words) {\n        // Simulation de génération pour tester l'interface\n        setTimeout(() => {\n            const simulatedResults = [];\n            \n            for (let i = 0; i < 5; i++) {\n                const shuffledWords = [...words].sort(() => Math.random() - 0.5);\n                const phrase = `Phrase simulée ${i + 1} avec ${shuffledWords.slice(0, 3).join(', ')}`;\n                \n                simulatedResults.push({\n                    text: phrase,\n                    keywords: shuffledWords.slice(0, 4),\n                    audioUrl: this.generateDummyAudio(phrase),\n                    duration_seconds: 3 + Math.random() * 4\n                });\n            }\n            \n            this.handleGenerationResults(simulatedResults);\n        }, 2000);\n    }\n    \n    generateDummyAudio(text) {\n        // Générer un fichier audio factice pour les tests\n        // En production, ceci viendrait du serveur\n        return `data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQQAAAABAAEBAAGBhWlAQlEAAGEtAMU=`;\n    }\n    \n    handleWebSocketMessage(event) {\n        try {\n            const data = JSON.parse(event.data);\n            \n            switch (data.type) {\n                case 'generation_complete':\n                    this.handleGenerationResults(data.results);\n                    break;\n                    \n                case 'generation_error':\n                    this.updateStatus('generation', 'Erreur de génération', 'error');\n                    this.showNotification('Erreur lors de la génération', 'error');\n                    break;\n                    \n                case 'audio_ready':\n                    this.handleAudioReady(data);\n                    break;\n                    \n                default:\n                    console.log('📨 Message WebSocket non géré:', data);\n            }\n        } catch (error) {\n            console.error('❌ Erreur parsing WebSocket:', error);\n        }\n    }\n    \n    handleGenerationResults(results) {\n        console.log('🎉 Résultats reçus:', results.length, 'phrases');\n        \n        this.updateStatus('generation', `${results.length} phrases générées`, 'success');\n        \n        // Ajouter chaque résultat au player\n        results.forEach((result, index) => {\n            const metadata = {\n                phrases: [{ text: result.text }],\n                keywords: result.keywords || [],\n                duration_seconds: result.duration_seconds || 3,\n                timestamp: new Date().toLocaleTimeString()\n            };\n            \n            this.audioPlayer.addTrack(result.audioUrl, metadata);\n        });\n        \n        this.showNotification(`${results.length} nouvelles phrases ajoutées !`, 'success');\n    }\n    \n    handleAudioReady(data) {\n        console.log('🎵 Audio prêt:', data.filename);\n        // Mettre à jour l'URL audio si nécessaire\n    }\n    \n    setVisualizationMode(mode) {\n        // Mettre à jour les boutons\n        document.querySelectorAll('.viz-mode-btn').forEach(btn => {\n            btn.classList.toggle('active', btn.dataset.mode === mode);\n        });\n        \n        // Changer le mode du visualisateur\n        this.audioVisualizer.setMode(mode);\n        \n        console.log(`🎨 Mode visualisation: ${mode}`);\n    }\n    \n    updateUI() {\n        // Mettre à jour l'affichage des mots sélectionnés\n        const display = document.getElementById('selected-words-display');\n        if (this.selectedWords.size === 0) {\n            display.innerHTML = '<em>Aucun mot sélectionné</em>';\n        } else {\n            const wordsArray = Array.from(this.selectedWords);\n            display.innerHTML = wordsArray.map(word => \n                `<span class=\"selected-word-tag\">${word}</span>`\n            ).join('');\n        }\n        \n        // Activer/désactiver le bouton de génération\n        const generateBtn = document.getElementById('generate-phrase');\n        generateBtn.disabled = this.selectedWords.size === 0;\n    }\n    \n    updateStatus(type, text, state) {\n        const statusElement = document.getElementById(`${type}-status`);\n        if (!statusElement) return;\n        \n        const indicator = statusElement.querySelector('.status-indicator');\n        const textElement = statusElement.querySelector('.status-text');\n        \n        if (textElement) {\n            textElement.textContent = text;\n        }\n        \n        if (indicator) {\n            indicator.className = 'status-indicator';\n            if (state === true || state === 'success') {\n                indicator.classList.add('success');\n            } else if (state === false || state === 'error') {\n                indicator.classList.add('error');\n            } else if (state === 'loading') {\n                indicator.classList.add('loading');\n            }\n        }\n    }\n    \n    showNotification(message, type = 'info') {\n        // Créer une notification temporaire\n        const notification = document.createElement('div');\n        notification.className = `notification ${type}`;\n        notification.innerHTML = `\n            <span class=\"notification-icon\">${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}</span>\n            <span class=\"notification-message\">${message}</span>\n        `;\n        \n        // Ajouter au body\n        document.body.appendChild(notification);\n        \n        // Animation d'entrée\n        requestAnimationFrame(() => {\n            notification.classList.add('show');\n        });\n        \n        // Supprimer après 4 secondes\n        setTimeout(() => {\n            notification.classList.remove('show');\n            setTimeout(() => {\n                if (notification.parentNode) {\n                    notification.parentNode.removeChild(notification);\n                }\n            }, 300);\n        }, 4000);\n    }\n    \n    // API publique\n    getSelectedWords() {\n        return Array.from(this.selectedWords);\n    }\n    \n    getAudioPlayer() {\n        return this.audioPlayer;\n    }\n    \n    getSpiderSemantic() {\n        return this.spiderSemantic;\n    }\n    \n    getAudioVisualizer() {\n        return this.audioVisualizer;\n    }\n}\n\n// Initialisation globale\nlet audioApp;\n\ndocument.addEventListener('DOMContentLoaded', () => {\n    audioApp = new AudioApp();\n    console.log('🎵 Application initialisée');\n});\n\n// Export global\nwindow.audioApp = audioApp;