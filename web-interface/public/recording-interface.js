/* ===========================
   INTERFACE D'ENREGISTREMENT AUDIO
   UI pour contributions usagers
   =========================== */

class RecordingInterface {
    constructor() {
        this.recorder = null;
        this.audioData = null;
        this.isUploading = false;
        this.currentJobId = null;
        
        this.init();
    }

    /* ===========================
       INITIALISATION
       =========================== */

    init() {
        this.recorder = new AudioRecorder();
        this.createUI();
        this.attachEventListeners();
        
        // Callbacks du recorder
        this.recorder.onTimerUpdate = (duration) => {
            this.updateTimer(duration);
        };
        
        this.recorder.onComplete = (audioData) => {
            this.handleRecordingComplete(audioData);
        };
    }

    /* ===========================
       CRÉATION DE L'UI
       =========================== */

    createUI() {
        const html = `
            <div class="recording-interface" id="recording-interface">
                <div class="recording-overlay" id="recording-overlay">
                    <div class="recording-panel">
                        <div class="recording-header">
                            <h2>◉ contribuer</h2>
                        </div>
                        
                        <!-- État initial -->
                        <div class="recording-state" data-state="ready" id="recording-state">
                            <div class="recording-ready">
                                <div class="mic-icon">◉</div>
                                <p class="instruction">partagez votre voix sur le thème de l'amour</p>
                                <button class="record-start-btn" id="record-start-btn">
                                    commencer
                                </button>
                            </div>
                            
                            <!-- État enregistrement -->
                            <div class="recording-active">
                                <div class="recording-indicator">
                                    <div class="pulse-dot"></div>
                                    <span class="recording-timer" id="recording-timer">0:00</span>
                                </div>
                                <div class="waveform-viz" id="waveform-viz"></div>
                                <div class="recording-controls">
                                    <button class="record-pause-btn" id="record-pause-btn">
                                        <span>‖</span> pause
                                    </button>
                                    <button class="record-stop-btn" id="record-stop-btn">
                                        <span>■</span> terminer
                                    </button>
                                    <button class="record-cancel-btn" id="record-cancel-btn">
                                        <span>×</span> annuler
                                    </button>
                                </div>
                            </div>
                            
                            <!-- État lecture -->
                            <div class="recording-preview">
                                <div class="preview-info">
                                    <p>enregistrement terminé</p>
                                    <span class="preview-duration" id="preview-duration">0:00</span>
                                </div>
                                <audio controls class="preview-player" id="preview-player"></audio>
                                <div class="preview-actions">
                                    <button class="preview-retry-btn" id="preview-retry-btn">
                                        <span>↻</span> recommencer
                                    </button>
                                    <button class="preview-upload-btn" id="preview-upload-btn">
                                        <span>→</span> envoyer
                                    </button>
                                </div>
                            </div>
                            
                            <!-- État upload -->
                            <div class="recording-upload">
                                <div class="upload-progress">
                                    <div class="spinner"></div>
                                    <p id="upload-status">envoi en cours...</p>
                                </div>
                            </div>
                            
                            <!-- État traitement -->
                            <div class="recording-processing">
                                <div class="processing-steps">
                                    <div class="step" data-step="upload">
                                        <span class="step-icon">↑</span>
                                        <span class="step-label">envoi</span>
                                    </div>
                                    <div class="step" data-step="transcription">
                                        <span class="step-icon">⋯</span>
                                        <span class="step-label">transcription</span>
                                    </div>
                                    <div class="step" data-step="semantic">
                                        <span class="step-icon">♡</span>
                                        <span class="step-label">analyse</span>
                                    </div>
                                </div>
                                <p class="processing-message" id="processing-message">
                                    traitement en cours...
                                </p>
                            </div>
                            
                            <!-- État succès -->
                            <div class="recording-success">
                                <div class="success-icon">✓</div>
                                <h3>contribution reçue</h3>
                                <p class="success-message">
                                    votre enregistrement a été transcrit et analysé.
                                    merci pour votre contribution.
                                </p>
                                <div class="success-details" id="success-details"></div>
                                <button class="success-close-btn" id="success-close-btn">
                                    fermer
                                </button>
                            </div>
                            
                            <!-- État erreur -->
                            <div class="recording-error">
                                <div class="error-icon">!</div>
                                <h3>erreur</h3>
                                <p class="error-message" id="error-message"></p>
                                <button class="error-retry-btn" id="error-retry-btn">
                                    réessayer
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', html);
    }

    /* ===========================
       ÉVÉNEMENTS
       =========================== */

    attachEventListeners() {
        // Boutons de contrôle
        document.getElementById('record-start-btn')?.addEventListener('click', () => {
            this.startRecording();
        });
        
        document.getElementById('record-pause-btn')?.addEventListener('click', () => {
            this.togglePause();
        });
        
        document.getElementById('record-stop-btn')?.addEventListener('click', () => {
            this.stopRecording();
        });
        
        document.getElementById('record-cancel-btn')?.addEventListener('click', () => {
            this.cancelRecording();
        });
        
        document.getElementById('preview-retry-btn')?.addEventListener('click', () => {
            this.retryRecording();
        });
        
        document.getElementById('preview-upload-btn')?.addEventListener('click', () => {
            this.uploadRecording();
        });
        
        document.getElementById('success-close-btn')?.addEventListener('click', () => {
            this.close();
        });
        
        document.getElementById('error-retry-btn')?.addEventListener('click', () => {
            this.retryRecording();
        });
        
        // Fermer avec overlay
        document.getElementById('recording-overlay')?.addEventListener('click', (e) => {
            if (e.target.id === 'recording-overlay') {
                this.close();
            }
        });
    }

    /* ===========================
       CONTRÔLES D'ENREGISTREMENT
       =========================== */

    async startRecording() {
        try {
            await this.recorder.startRecording();
            this.setState('recording');
        } catch (error) {
            this.showError(error.message);
        }
    }

    togglePause() {
        if (this.recorder.isPaused) {
            this.recorder.resumeRecording();
            document.getElementById('record-pause-btn').innerHTML = '<span>⏸</span> Pause';
        } else {
            this.recorder.pauseRecording();
            document.getElementById('record-pause-btn').innerHTML = '<span>▶</span> Reprendre';
        }
    }

    stopRecording() {
        this.recorder.stopRecording();
        // L'état changera automatiquement via onComplete
    }

    cancelRecording() {
        this.recorder.cancelRecording();
        this.setState('ready');
    }

    retryRecording() {
        this.audioData = null;
        this.setState('ready');
    }

    /* ===========================
       TRAITEMENT ENREGISTREMENT
       =========================== */

    handleRecordingComplete(audioData) {
        this.audioData = audioData;
        
        // Mettre à jour le lecteur de prévisualisation
        const player = document.getElementById('preview-player');
        player.src = audioData.url;
        
        const durationEl = document.getElementById('preview-duration');
        durationEl.textContent = this.recorder.formatDuration(audioData.duration);
        
        this.setState('preview');
    }

    /* ===========================
       UPLOAD ET TRAITEMENT
       =========================== */

    async uploadRecording() {
        if (!this.audioData || this.isUploading) return;
        
        this.isUploading = true;
        this.setState('uploading');
        
        try {
            // Upload
            const uploadResult = await this.recorder.uploadRecording(this.audioData, {
                source: 'web-interface',
                language: 'fr'
            });
            
            console.log('Upload réussi:', uploadResult);
            this.currentJobId = uploadResult.jobId;
            
            // Passer à l'état de traitement
            this.setState('processing');
            this.updateProcessingStep('upload', 'completed');
            
            // Polling du statut de traitement
            await this.pollProcessingStatus(uploadResult.jobId);
            
        } catch (error) {
            console.error('Erreur upload:', error);
            this.showError(`Erreur lors de l'envoi: ${error.message}`);
        } finally {
            this.isUploading = false;
        }
    }

    async pollProcessingStatus(jobId) {
        const maxAttempts = 120; // 10 minutes max (5s * 120)
        let attempts = 0;
        
        const poll = async () => {
            try {
                const response = await fetch(`/api/processing-status/${jobId}`);
                const status = await response.json();
                
                console.log('Statut traitement:', status);
                
                // Mettre à jour l'UI selon le statut
                if (status.progress) {
                    this.updateProcessingMessage(status.progress.message);
                    this.updateProcessingStep(status.progress.step, 'active');
                }
                
                if (status.status === 'completed') {
                    this.updateProcessingStep('semantic', 'completed');
                    this.showSuccess(status);
                    return;
                }
                
                if (status.status === 'error') {
                    this.showError(status.error || 'Erreur de traitement');
                    return;
                }
                
                // Continuer le polling
                attempts++;
                if (attempts < maxAttempts) {
                    setTimeout(poll, 5000); // Poll toutes les 5 secondes
                } else {
                    this.showError('Délai de traitement dépassé');
                }
                
            } catch (error) {
                console.error('Erreur polling:', error);
                this.showError('Erreur lors de la vérification du statut');
            }
        };
        
        // Démarrer le polling
        setTimeout(poll, 2000); // Premier check après 2s
    }

    /* ===========================
       MISE À JOUR DE L'UI
       =========================== */

    setState(state) {
        const stateEl = document.getElementById('recording-state');
        stateEl.setAttribute('data-state', state);
    }

    updateTimer(duration) {
        const timerEl = document.getElementById('recording-timer');
        if (timerEl) {
            timerEl.textContent = this.recorder.formatDuration(duration);
        }
    }

    updateProcessingMessage(message) {
        const messageEl = document.getElementById('processing-message');
        if (messageEl) {
            messageEl.textContent = message;
        }
    }

    updateProcessingStep(step, status) {
        const stepEl = document.querySelector(`.step[data-step="${step}"]`);
        if (stepEl) {
            stepEl.setAttribute('data-status', status);
        }
    }

    showSuccess(result) {
        const detailsEl = document.getElementById('success-details');
        if (detailsEl) {
            let html = '';
            
            // Afficher le texte transcrit
            if (result.transcriptionText) {
                html += `
                    <div class="transcription-text">
                        <p class="text-label">texte transcrit :</p>
                        <p class="text-content">${result.transcriptionText}</p>
                    </div>
                `;
            }
            
            // Afficher l'analyse sémantique
            if (result.semanticAnalysis) {
                const analysis = result.semanticAnalysis;
                html += `
                    <div class="semantic-analysis">
                        <p class="text-label">analyse sémantique :</p>
                `;
                
                // Extraire le type dominant depuis love_analysis
                if (analysis.love_analysis) {
                    const loveAnalysis = analysis.love_analysis;
                    
                    // Trouver le type dominant
                    if (loveAnalysis.statistics_by_type) {
                        const types = Object.entries(loveAnalysis.statistics_by_type)
                            .map(([type, stats]) => ({ type, score: stats.average_score }))
                            .sort((a, b) => b.score - a.score);
                        
                        if (types.length > 0) {
                            const dominant = types[0];
                            html += `<p class="analysis-item"><span class="item-label">type dominant :</span> ${dominant.type} (${(dominant.score * 100).toFixed(0)}%)</p>`;
                            
                            // Afficher les autres types significatifs
                            const others = types.slice(1, 3).filter(t => t.score > 0.2);
                            if (others.length > 0) {
                                html += `<p class="analysis-item"><span class="item-label">autres :</span> ${others.map(t => `${t.type} (${(t.score * 100).toFixed(0)}%)`).join(', ')}</p>`;
                            }
                        }
                    }
                    
                    // Afficher le taux de couverture
                    if (loveAnalysis.love_coverage_percentage !== undefined) {
                        html += `<p class="analysis-item"><span class="item-label">contenu amour :</span> ${loveAnalysis.love_coverage_percentage.toFixed(0)}%</p>`;
                    }
                }
                
                html += `</div>`;
            }
            
            detailsEl.innerHTML = html;
        }
        
        this.setState('success');
    }

    showError(message) {
        const errorEl = document.getElementById('error-message');
        if (errorEl) {
            errorEl.textContent = message;
        }
        
        this.setState('error');
    }

    /* ===========================
       GESTION DE L'INTERFACE
       =========================== */

    open() {
        const interfaceEl = document.getElementById('recording-interface');
        if (interfaceEl) {
            interfaceEl.classList.add('active');
            this.setState('ready');
        }
    }

    close() {
        // Arrêter l'enregistrement si en cours
        if (this.recorder.isRecording) {
            this.recorder.cancelRecording();
        }
        
        // Nettoyer l'audio data
        if (this.audioData?.url) {
            URL.revokeObjectURL(this.audioData.url);
        }
        
        const interfaceEl = document.getElementById('recording-interface');
        if (interfaceEl) {
            interfaceEl.classList.remove('active');
        }
        
        // Reset
        this.audioData = null;
        this.currentJobId = null;
    }
}

/* ===========================
   INITIALISATION GLOBALE
   =========================== */

// Ajouter au contexte global
window.RecordingInterface = RecordingInterface;

// Fonction d'aide pour ouvrir l'interface
window.openRecordingInterface = function() {
    if (!window.recordingInterface) {
        window.recordingInterface = new RecordingInterface();
    }
    window.recordingInterface.open();
};
