/* ===========================
   MODULE D'ENREGISTREMENT AUDIO
   Capture audio pour contributions usagers
   =========================== */

class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
        this.isPaused = false;
        this.startTime = null;
        this.pausedTime = 0;
        this.recordingTimer = null;
    }

    /* ===========================
       INITIALISATION
       =========================== */

    async initialize() {
        try {
            // Demander permission microphone
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100
                } 
            });

            // Créer MediaRecorder avec format optimal
            const mimeType = this.getSupportedMimeType();
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: mimeType,
                audioBitsPerSecond: 128000
            });

            // Collecter les données audio
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            // Gestion de la fin d'enregistrement
            this.mediaRecorder.onstop = () => {
                this.onRecordingComplete();
            };

            console.log('🎙️ Enregistreur audio initialisé avec', mimeType);
            return true;

        } catch (error) {
            console.error('❌ Erreur initialisation microphone:', error);
            throw new Error('Impossible d\'accéder au microphone. Vérifiez les permissions.');
        }
    }

    /* ===========================
       FORMATS AUDIO SUPPORTÉS
       =========================== */

    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/mp4'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }

        return ''; // Utiliser le format par défaut
    }

    getFileExtension() {
        const mimeType = this.mediaRecorder?.mimeType || 'audio/webm';
        if (mimeType.includes('webm')) return 'webm';
        if (mimeType.includes('ogg')) return 'ogg';
        if (mimeType.includes('mp4')) return 'mp4';
        return 'webm';
    }

    /* ===========================
       CONTRÔLES D'ENREGISTREMENT
       =========================== */

    async startRecording() {
        if (!this.mediaRecorder) {
            await this.initialize();
        }

        this.audioChunks = [];
        this.startTime = Date.now();
        this.pausedTime = 0;
        this.isRecording = true;
        this.isPaused = false;

        this.mediaRecorder.start(100); // Collecter données toutes les 100ms
        this.startTimer();

        console.log('🔴 Enregistrement démarré');
    }

    pauseRecording() {
        if (this.isRecording && !this.isPaused) {
            this.mediaRecorder.pause();
            this.isPaused = true;
            this.pausedTime = Date.now();
            this.stopTimer();
            console.log('⏸️ Enregistrement en pause');
        }
    }

    resumeRecording() {
        if (this.isRecording && this.isPaused) {
            this.mediaRecorder.resume();
            this.isPaused = false;
            const pauseDuration = Date.now() - this.pausedTime;
            this.startTime += pauseDuration;
            this.startTimer();
            console.log('▶️ Enregistrement repris');
        }
    }

    stopRecording() {
        if (this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.isPaused = false;
            this.stopTimer();
            console.log('⏹️ Enregistrement arrêté');
        }
    }

    cancelRecording() {
        if (this.isRecording) {
            this.stopRecording();
            this.audioChunks = [];
            console.log('❌ Enregistrement annulé');
        }
    }

    /* ===========================
       TIMER D'ENREGISTREMENT
       =========================== */

    startTimer() {
        this.recordingTimer = setInterval(() => {
            const duration = this.getRecordingDuration();
            this.onTimerUpdate(duration);
        }, 100);
    }

    stopTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }

    getRecordingDuration() {
        if (!this.startTime) return 0;
        return (Date.now() - this.startTime) / 1000;
    }

    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    /* ===========================
       TRAITEMENT AUDIO
       =========================== */

    onRecordingComplete() {
        if (this.audioChunks.length === 0) {
            console.warn('⚠️ Aucune donnée audio enregistrée');
            return;
        }

        // Créer le blob audio
        const mimeType = this.mediaRecorder.mimeType;
        const audioBlob = new Blob(this.audioChunks, { type: mimeType });

        // Créer URL pour lecture
        const audioUrl = URL.createObjectURL(audioBlob);

        console.log('✅ Enregistrement terminé:', {
            duration: this.formatDuration(this.getRecordingDuration()),
            size: `${(audioBlob.size / 1024).toFixed(2)} KB`,
            type: mimeType
        });

        // Callback avec les données
        if (this.onComplete) {
            this.onComplete({
                blob: audioBlob,
                url: audioUrl,
                duration: this.getRecordingDuration(),
                mimeType: mimeType,
                extension: this.getFileExtension()
            });
        }
    }

    /* ===========================
       UPLOAD VERS SERVEUR
       =========================== */

    async uploadRecording(audioData, metadata = {}) {
        const formData = new FormData();
        
        // Créer nom de fichier unique
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `contribution_${timestamp}.${audioData.extension}`;
        
        // Ajouter fichier audio
        formData.append('audio', audioData.blob, filename);
        
        // Ajouter métadonnées
        formData.append('metadata', JSON.stringify({
            duration: audioData.duration,
            mimeType: audioData.mimeType,
            timestamp: new Date().toISOString(),
            ...metadata
        }));

        try {
            console.log('📤 Upload en cours:', filename);
            
            const response = await fetch('/api/upload-contribution', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const result = await response.json();
            console.log('✅ Upload réussi:', result);
            
            return result;

        } catch (error) {
            console.error('❌ Erreur upload:', error);
            throw error;
        }
    }

    /* ===========================
       NETTOYAGE
       =========================== */

    cleanup() {
        this.stopTimer();
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        
        console.log('🧹 Enregistreur audio nettoyé');
    }

    /* ===========================
       CALLBACKS (à surcharger)
       =========================== */

    onTimerUpdate(duration) {
        // À surcharger pour mettre à jour l'UI
    }

    onComplete(audioData) {
        // À surcharger pour traiter l'enregistrement
    }
}

/* ===========================
   EXPORT
   =========================== */

if (typeof module !== 'undefined' && module.exports) {
    module.exports = AudioRecorder;
}
