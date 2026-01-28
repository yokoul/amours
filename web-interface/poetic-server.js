/* ===========================
   SERVEUR POÉTIQUE
   Interface minimaliste pour performance live
   =========================== */

const express = require('express');
const https = require('https');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs').promises;
const fsSync = require('fs');
const cors = require('cors');
const multer = require('multer');
const crypto = require('crypto');

class PoeticServer {
    constructor() {
        this.app = express();
        this.port = 3000;
        
        // Chemins relatifs calculés automatiquement
        this.projectRoot = path.resolve(__dirname, '..');
        this.pythonPath = path.join(this.projectRoot, '.venv', 'bin', 'python');
        
        // Stockage des jobs de traitement
        this.processingJobs = new Map();
        
        this.setup();
    }
    
    setup() {
        // Middleware minimaliste
        this.app.use(cors());
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.static('public'));
        
        // Routes artistiques
        this.setupRoutes();
        
        console.log('🎭 Serveur poétique configuré');
    }
    
    setupRoutes() {
        // Interface poétique principale
        this.app.get('/', (req, res) => {
            res.sendFile(path.join(__dirname, 'public', 'poetic-interface.html'));
        });
        
        // API pour récupération des mots
        this.app.get('/api/words', async (req, res) => {
            try {
                const words = await this.getInspirationalWords();
                res.json(words);
            } catch (error) {
                console.error('Erreur mots:', error);
                res.status(500).json({ error: 'Impossible de récupérer les mots' });
            }
        });
        
        // API pour générer un MP3 individuel à la demande
        this.app.post('/api/generate-phrase-audio/:phraseIndex', async (req, res) => {
            try {
                const phraseIndex = parseInt(req.params.phraseIndex);
                
                // Récupérer les données de la phrase depuis le body
                const { phrase } = req.body;
                
                if (!phrase) {
                    return res.status(400).json({ error: 'Données de phrase manquantes' });
                }
                
                console.log(`🎵 Génération MP3 à la demande pour phrase ${phraseIndex + 1}`);
                
                // Appeler le script Python pour générer le fichier
                const result = await this.generateSinglePhraseAudio(phrase, phraseIndex);
                res.json(result);
                
            } catch (error) {
                console.error('Erreur génération phrase audio:', error);
                res.status(500).json({ error: error.message });
            }
        });
        
        // API pour génération poétique
        this.app.post('/api/generate', async (req, res) => {
            try {
                const { words, count = 3, includeNext = 0 } = req.body; // Par défaut 3 phrases, mode normal
                
                if (!words || words.length < 2) {
                    return res.status(400).json({ 
                        error: 'Au moins 2 mots nécessaires' 
                    });
                }
                
                const modeText = includeNext > 0 ? ` (mode étendu +${includeNext})` : '';
                console.log(`🎪 Génération demandée: ${count} phrases avec mots: ${words.join(', ')}${modeText}`);
                
                const result = await this.generatePoetry(words, count, includeNext);
                res.json(result);
                
            } catch (error) {
                console.error('Erreur génération:', error);
                res.status(500).json({ 
                    error: 'Erreur lors de la création poétique' 
                });
            }
        });
        
        // API pour l'archive
        this.app.get('/api/archive', async (req, res) => {
            try {
                const archive = await this.getArchive();
                res.json(archive);
            } catch (error) {
                res.status(500).json({ error: 'Erreur archive' });
            }
        });
        
        // API pour upload de contributions audio
        this.app.post('/api/upload-contribution', this.uploadMiddleware(), async (req, res) => {
            try {
                await this.handleAudioContribution(req, res);
            } catch (error) {
                console.error('Erreur upload:', error);
                res.status(500).json({ error: 'Erreur lors de l\'upload' });
            }
        });
        
        // API pour vérifier le statut de traitement
        this.app.get('/api/processing-status/:jobId', async (req, res) => {
            try {
                const status = await this.getProcessingStatus(req.params.jobId);
                res.json(status);
            } catch (error) {
                res.status(500).json({ error: 'Erreur récupération statut' });
            }
        });
        
        // API pour recherche dans les transcriptions
        this.app.get('/api/search', async (req, res) => {
            try {
                const query = req.query.q || req.query.query;
                const limit = parseInt(req.query.limit) || 10;
                const offset = parseInt(req.query.offset) || 0;
                
                if (!query || query.trim().length < 2) {
                    return res.status(400).json({ 
                        error: 'La requête doit contenir au moins 2 caractères' 
                    });
                }
                
                console.log(`🔍 Recherche: "${query}" (limit: ${limit}, offset: ${offset})`);
                
                const results = await this.searchTranscriptions(query, limit, offset);
                res.json(results);
                
            } catch (error) {
                console.error('Erreur recherche:', error);
                res.status(500).json({ 
                    error: 'Erreur lors de la recherche',
                    details: error.message 
                });
            }
        });
        
        // API pour extraire et télécharger un segment audio de recherche
        this.app.post('/api/extract-search-audio', async (req, res) => {
            try {
                const { audio_path, start_time, end_time } = req.body;
                
                if (!audio_path || start_time === undefined || end_time === undefined) {
                    return res.status(400).json({ 
                        error: 'Paramètres manquants (audio_path, start_time, end_time requis)' 
                    });
                }
                
                console.log(`🎵 Extraction audio: ${audio_path} (${start_time}s → ${end_time}s)`);
                
                const result = await this.extractAudioSegment(audio_path, start_time, end_time);
                res.json(result);
                
            } catch (error) {
                console.error('Erreur extraction audio:', error);
                res.status(500).json({ 
                    error: 'Erreur lors de l\'extraction audio',
                    details: error.message 
                });
            }
        });
        
        // Servir les fichiers audio générés (montages et extraits individuels)
        // Les montages sont dans output_mix_play, les extraits dans web-interface/public/audio
        this.app.use('/audio', express.static(path.join(this.projectRoot, 'output_mix_play')));
        this.app.use('/audio', express.static(path.join(__dirname, 'public', 'audio')));
        
        // Servir les fichiers audio sources (pour les extraits de recherche)
        this.app.use('/audio-sources', express.static(path.join(this.projectRoot, 'audio')));
        
        // Gestion d'erreur artistique
        this.app.use((err, req, res, next) => {
            console.error('💥 Erreur serveur:', err);
            res.status(500).json({ 
                error: 'Erreur interne du serveur poétique' 
            });
        });
    }
    
    /* ===========================
       GÉNÉRATION DE MOTS INSPIRANTS
       =========================== */
    
    async getInspirationalWords() {
        // Pool de mots réellement présents dans les transcriptions audio
        // Liste nettoyée : 90 mots (doublons et variations retirés)
        const loveWords = [
            'amour', 'aimer', 'amoureux', 'amoureuse', 'amitié',
            'passion', 'désir', 'tendresse', 'émotion', 'sentiment',
            'joie', 'bonheur', 'tristesse', 'peur', 'colère',
            'jalousie', 'haine', 'espoir', 'pensée', 'rêve',
            'cœur', 'corps', 'sang', 'main', 'yeux',
            'visage', 'voix', 'sourire', 'regard', 'esprit',
            'famille', 'mère', 'père', 'enfant', 'frère',
            'sœur', 'couple', 'amant', 'mariage', 'divorce',
            'rencontre', 'séparation', 'absence', 'présence', 'distance',
            'attente', 'souvenir', 'mémoire', 'nostalgie', 'passé',
            'présent', 'futur', 'hier', 'instant', 'moment',
            'temps', 'toujours', 'jamais', 'mort', 'vie',
            'manque', 'besoin', 'envie', 'vide', 'plein',
            'grand', 'petit', 'fort', 'léger', 'profond',
            'chaud', 'froid', 'lumière', 'terre', 'lieu',
            'maison', 'chambre', 'jardin', 'ville', 'chemin',
            'dire', 'parler', 'voir', 'regarder', 'entendre',
            'écouter', 'sentir', 'toucher', 'venir', 'partir',
            'rester', 'tomber', 'marcher', 'devenir', 'polyamour',
            'trahison', 'fidélité', 'odeur', 'couleur', 'chant',
            'musique', 'silence', 'nature', 'mer', 'ciel',
            'étoile', 'lune', 'soleil', 'chien', 'chat', 'fleur'
        ];
        
        // Mélanger aléatoirement
        const shuffled = loveWords.sort(() => 0.5 - Math.random());
        
        // Prendre 15 mots aléatoires + toujours "amour" en premier
        const randomWords = shuffled.slice(0, 15);
        
        return ['amour', ...randomWords];
    }
    
    /* ===========================
       GÉNÉRATION POÉTIQUE
       =========================== */
    
    async generateSinglePhraseAudio(phraseData, phraseIndex) {
        return new Promise((resolve, reject) => {
            const script = path.join(__dirname, 'generate_single_phrase_audio.py');
            
            // Passer les données de la phrase en JSON
            const pythonArgs = [
                script,
                JSON.stringify(phraseData),
                phraseIndex.toString()
            ];
            
            const python = spawn(this.pythonPath, pythonArgs);
            
            let output = '';
            let error = '';
            
            python.stdout.on('data', (data) => {
                output += data.toString('utf8');
            });
            
            python.stderr.on('data', (data) => {
                error += data.toString('utf8');
            });
            
            python.on('close', (code) => {
                if (code !== 0) {
                    console.error('❌ Erreur Python génération phrase:', error);
                    reject(new Error('Erreur lors de la génération du fichier audio'));
                    return;
                }
                
                try {
                    const result = JSON.parse(output.trim());
                    if (result.success) {
                        resolve(result);
                    } else {
                        reject(new Error(result.error || 'Génération échouée'));
                    }
                } catch (e) {
                    console.error('❌ Erreur parsing JSON:', e, '\nOutput:', output);
                    reject(new Error('Erreur de parsing de la réponse'));
                }
            });
        });
    }
    
    async generatePoetry(words, count = 3, includeNext = 0) {
        return new Promise((resolve, reject) => {
            // Utiliser le script web_phrase_generator.py (optimisé pour le web)
            const script = path.join(__dirname, 'web_phrase_generator.py');
            
            // Construire les arguments Python
            const pythonArgs = [script, count.toString()];
            
            // Ajouter le paramètre --include-next si > 0
            if (includeNext > 0) {
                pythonArgs.push(`--include-next=${includeNext}`);
            }
            
            // Ajouter les mots
            pythonArgs.push(...words);
            
            const python = spawn(this.pythonPath, pythonArgs, {
                cwd: this.projectRoot,
                env: { 
                    ...process.env, 
                    PYTHONPATH: this.projectRoot,
                    PYTHONIOENCODING: 'utf-8',
                    LANG: 'en_US.UTF-8'
                }
            });
            
            let output = '';
            let error = '';
            
            python.stdout.on('data', (data) => {
                output += data.toString('utf8');
            });
            
            python.stderr.on('data', (data) => {
                error += data.toString('utf8');
            });
            
            python.on('close', async (code) => {
                if (code !== 0) {
                    console.error('❌ Erreur Python génération:', error);
                    reject(new Error('Erreur lors de la génération'));
                    return;
                }
                
                try {
                    // Nettoyer l'output pour extraire le JSON
                    const lines = output.split('\n').filter(line => line.trim());
                    let jsonLine = '';
                    
                    for (const line of lines) {
                        if (line.trim().startsWith('{') && line.includes('success')) {
                            jsonLine = line;
                            break;
                        }
                    }
                    
                    if (!jsonLine) {
                        throw new Error('Pas de JSON trouvé dans la sortie');
                    }
                    
                    const result = JSON.parse(jsonLine);
                    console.log('✅ Résultat Python:', result);
                    
                    if (!result.success) {
                        throw new Error(result.error || 'Génération échouée');
                    }
                    
                    // Gérer l'audio
                    let audioUrl = null;
                    
                    if (result.audio_base64) {
                        // Sauvegarder l'audio en fichier
                        const audioId = `poetic_${result.timestamp}`;
                        const audioBuffer = Buffer.from(result.audio_base64, 'base64');
                        const audioPath = path.join(this.projectRoot, 'web-interface/public/audio', `${audioId}.mp3`);
                        
                        // Créer le dossier si nécessaire
                        const audioDir = path.dirname(audioPath);
                        await fs.mkdir(audioDir, { recursive: true });
                        await fs.writeFile(audioPath, audioBuffer);
                        
                        audioUrl = `/audio/${audioId}.mp3`;
                        console.log('🔊 Audio sauvegardé:', audioUrl);
                    } else if (result.audio_file) {
                        const fileName = result.audio_file.split('/').pop();
                        audioUrl = `/audio/${fileName}`;
                    } else if (result.audio_url) {
                        audioUrl = result.audio_url;
                    }
                    
                    resolve({
                        success: true,
                        audio_url: audioUrl,
                        audioFile: audioUrl, // Compatibilité
                        phrases: result.phrases || [],
                        phrase: result.phrases && result.phrases.length > 0 
                            ? result.phrases.map(p => p.text).join(' (...) ')
                            : `Création avec ${words.join(', ')}`,
                        keywords: words,
                        duration_seconds: result.duration_seconds,
                        timestamp: result.timestamp || Date.now(),
                        semantic_analysis: result.semantic_analysis || null
                    });
                    
                } catch (e) {
                    console.error('❌ Erreur parsing:', e);
                    console.error('📄 Output:', output.substring(0, 500));
                    reject(e);
                }
            });
        });
    }
    
    /* ===========================
       MIDDLEWARE UPLOAD
       =========================== */
    
    uploadMiddleware() {
        const storage = multer.diskStorage({
            destination: async (req, file, cb) => {
                const uploadDir = path.join(this.projectRoot, 'audio', 'contributions');
                await fs.mkdir(uploadDir, { recursive: true });
                cb(null, uploadDir);
            },
            filename: (req, file, cb) => {
                // Générer nom unique
                const uniqueId = crypto.randomBytes(8).toString('hex');
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                const ext = path.extname(file.originalname) || '.webm';
                cb(null, `contribution_${timestamp}_${uniqueId}${ext}`);
            }
        });
        
        return multer({ 
            storage,
            limits: { fileSize: 50 * 1024 * 1024 }, // 50 MB max
            fileFilter: (req, file, cb) => {
                const allowedTypes = ['audio/webm', 'audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/ogg', 'audio/mp4'];
                if (allowedTypes.includes(file.mimetype) || file.mimetype.startsWith('audio/')) {
                    cb(null, true);
                } else {
                    cb(new Error('Type de fichier non supporté'));
                }
            }
        }).single('audio');
    }
    
    /* ===========================
       TRAITEMENT CONTRIBUTIONS AUDIO
       =========================== */
    
    async handleAudioContribution(req, res) {
        if (!req.file) {
            return res.status(400).json({ error: 'Aucun fichier audio fourni' });
        }
        
        const audioPath = req.file.path;
        const metadata = req.body.metadata ? JSON.parse(req.body.metadata) : {};
        
        console.log('🎤 Nouvelle contribution reçue:', {
            file: req.file.filename,
            size: `${(req.file.size / 1024).toFixed(2)} KB`,
            duration: metadata.duration,
            mimetype: req.file.mimetype
        });
        
        // Créer un job ID unique
        const jobId = crypto.randomBytes(16).toString('hex');
        
        // Initialiser le job
        this.processingJobs.set(jobId, {
            status: 'queued',
            audioFile: req.file.filename,
            audioPath: audioPath,
            metadata: metadata,
            startTime: Date.now(),
            progress: {
                step: 'upload',
                message: 'Fichier reçu'
            }
        });
        
        // Répondre immédiatement avec le job ID
        res.json({
            success: true,
            jobId: jobId,
            message: 'Contribution reçue, traitement en cours...',
            audioFile: req.file.filename
        });
        
        // Lancer le traitement en arrière-plan
        this.processAudioContribution(jobId).catch(error => {
            console.error('❌ Erreur traitement contribution:', error);
            const job = this.processingJobs.get(jobId);
            if (job) {
                job.status = 'error';
                job.error = error.message;
            }
        });
    }
    
    /* ===========================
       PIPELINE DE TRAITEMENT
       =========================== */
    
    async processAudioContribution(jobId) {
        const job = this.processingJobs.get(jobId);
        if (!job) return;
        
        try {
            // Étape 1: Transcription
            job.status = 'processing';
            job.progress = { step: 'transcription', message: 'Transcription audio en cours...' };
            console.log('📝 Transcription démarrée pour', job.audioFile);
            
            const transcriptionResult = await this.transcribeAudio(job.audioPath);
            job.transcriptionFile = transcriptionResult.jsonFile;
            
            // Étape 2: Analyse sémantique
            job.progress = { step: 'semantic', message: 'Analyse sémantique en cours...' };
            console.log('❤️  Analyse sémantique démarrée');
            
            const semanticResult = await this.analyzeSemantics(transcriptionResult.jsonFile);
            job.semanticFile = semanticResult.jsonFile;
            
            // Terminé
            job.status = 'completed';
            job.progress = { step: 'completed', message: 'Traitement terminé avec succès' };
            job.completedTime = Date.now();
            job.processingDuration = (job.completedTime - job.startTime) / 1000;
            
            console.log('✅ Contribution traitée avec succès:', {
                jobId: jobId,
                duration: `${job.processingDuration.toFixed(1)}s`,
                transcription: path.basename(job.transcriptionFile),
                semantic: path.basename(job.semanticFile)
            });
            
        } catch (error) {
            console.error('❌ Erreur traitement:', error);
            job.status = 'error';
            job.error = error.message;
            job.progress = { step: 'error', message: error.message };
        }
    }
    
    /* ===========================
       TRANSCRIPTION AUDIO
       =========================== */
    
    async transcribeAudio(audioPath) {
        return new Promise((resolve, reject) => {
            const script = path.join(this.projectRoot, 'src', 'main_with_speakers.py');
            
            // Générer le chemin de sortie
            const audioFilename = path.basename(audioPath, path.extname(audioPath));
            const outputPath = path.join(
                this.projectRoot, 
                'output_transcription', 
                `${audioFilename}_with_speakers_complete.json`
            );
            
            const args = [
                script,
                '--input', audioPath,
                '--output', outputPath,
                '--model', 'medium',
                '--format', 'json',
                '--word-timestamps'
            ];
            
            console.log('🎯 Commande transcription:', this.pythonPath, args.join(' '));
            
            const python = spawn(this.pythonPath, args, {
                cwd: this.projectRoot,
                env: { 
                    ...process.env, 
                    PYTHONPATH: this.projectRoot,
                    PYTHONIOENCODING: 'utf-8'
                }
            });
            
            let output = '';
            let error = '';
            
            python.stdout.on('data', (data) => {
                const text = data.toString('utf8');
                output += text;
                console.log('📝', text.trim());
            });
            
            python.stderr.on('data', (data) => {
                const text = data.toString('utf8');
                error += text;
                console.log('⚠️', text.trim());
            });
            
            python.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Transcription échouée: ${error}`));
                    return;
                }
                
                // Le fichier JSON est maintenant à l'emplacement spécifié
                resolve({ jsonFile: outputPath, output });
            });
        });
    }
    
    /* ===========================
       ANALYSE SÉMANTIQUE
       =========================== */
    
    async analyzeSemantics(jsonFile) {
        return new Promise((resolve, reject) => {
            const script = path.join(this.projectRoot, 'analyze_love.py');
            
            // Générer le chemin de sortie pour l'analyse
            const baseFilename = path.basename(jsonFile, '.json');
            const outputPath = path.join(
                this.projectRoot, 
                'output_semantic', 
                `${baseFilename}_love_analysis.json`
            );
            
            const args = [
                script,
                '--input', jsonFile,
                '--output', outputPath,
                '--threshold', '0.15',
                '--semantic'
            ];
            
            console.log('🎯 Commande analyse:', this.pythonPath, args.join(' '));
            
            const python = spawn(this.pythonPath, args, {
                cwd: this.projectRoot,
                env: { 
                    ...process.env, 
                    PYTHONPATH: this.projectRoot,
                    PYTHONIOENCODING: 'utf-8'
                }
            });
            
            let output = '';
            let error = '';
            
            python.stdout.on('data', (data) => {
                const text = data.toString('utf8');
                output += text;
                console.log('❤️', text.trim());
            });
            
            python.stderr.on('data', (data) => {
                const text = data.toString('utf8');
                error += text;
                console.log('⚠️', text.trim());
            });
            
            python.on('close', (code) => {
                if (code !== 0) {
                    reject(new Error(`Analyse sémantique échouée: ${error}`));
                    return;
                }
                
                // Le script crée un répertoire avec le nom du fichier, puis met le JSON dedans
                // Le nom du fichier dans le répertoire utilise le baseFilename sans le suffixe _complete
                const cleanBasename = baseFilename.replace(/_complete$/, '');
                const actualJsonPath = path.join(
                    outputPath,
                    `${cleanBasename}_love_analysis_love_analysis.json`
                );
                
                resolve({ jsonFile: actualJsonPath, output });
            });
        });
    }
    
    /* ===========================
       STATUT DE TRAITEMENT
       =========================== */
    
    async getProcessingStatus(jobId) {
        const job = this.processingJobs.get(jobId);
        
        if (!job) {
            return { error: 'Job non trouvé' };
        }
        
        const response = {
            jobId: jobId,
            status: job.status,
            progress: job.progress,
            audioFile: job.audioFile
        };
        
        if (job.status === 'completed') {
            response.transcriptionFile = path.basename(job.transcriptionFile);
            response.semanticFile = path.basename(job.semanticFile);
            response.processingDuration = job.processingDuration;
            
            // Lire le contenu de la transcription
            try {
                const transcriptionData = JSON.parse(fsSync.readFileSync(job.transcriptionFile, 'utf-8'));
                response.transcriptionText = transcriptionData.transcription?.text || transcriptionData.text || '';
                response.words = transcriptionData.transcription?.words || transcriptionData.words || [];
            } catch (err) {
                console.error('❌ Erreur lecture transcription:', err);
            }
            
            // Lire le contenu de l'analyse sémantique
            try {
                const semanticData = JSON.parse(fsSync.readFileSync(job.semanticFile, 'utf-8'));
                response.semanticAnalysis = semanticData;
            } catch (err) {
                console.error('❌ Erreur lecture analyse:', err);
            }
        }
        
        if (job.status === 'error') {
            response.error = job.error;
        }
        
        return response;
    }
    
    /* ===========================
       MIDDLEWARE UPLOAD
       =========================== */
    
    uploadMiddleware() {
        const storage = multer.diskStorage({
            destination: async (req, file, cb) => {
                const uploadDir = path.join(this.projectRoot, 'audio', 'contributions');
                await fs.mkdir(uploadDir, { recursive: true });
                cb(null, uploadDir);
            },
            filename: (req, file, cb) => {
                // Générer nom unique
                const uniqueId = crypto.randomBytes(8).toString('hex');
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                const ext = path.extname(file.originalname) || '.webm';
                cb(null, `contribution_${timestamp}_${uniqueId}${ext}`);
            }
        });
        
        return multer({ 
            storage,
            limits: { fileSize: 50 * 1024 * 1024 }, // 50 MB max
            fileFilter: (req, file, cb) => {
                const allowedTypes = ['audio/webm', 'audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/ogg', 'audio/mp4'];
                if (allowedTypes.includes(file.mimetype) || file.mimetype.startsWith('audio/')) {
                    cb(null, true);
                } else {
                    cb(new Error('Type de fichier non supporté'));
                }
            }
        }).single('audio');
    }
    
    /* ===========================
       TRAITEMENT CONTRIBUTIONS AUDIO
       =========================== */
    
    async handleAudioContribution(req, res) {
        if (!req.file) {
            return res.status(400).json({ error: 'Aucun fichier audio fourni' });
        }
        
        const audioPath = req.file.path;
        const metadata = req.body.metadata ? JSON.parse(req.body.metadata) : {};
        
        console.log('🎤 Nouvelle contribution reçue:', {
            file: req.file.filename,
            size: `${(req.file.size / 1024).toFixed(2)} KB`,
            duration: metadata.duration,
            mimetype: req.file.mimetype
        });
        
        // Créer un job ID unique
        const jobId = crypto.randomBytes(16).toString('hex');
        
        // Initialiser le job
        this.processingJobs.set(jobId, {
            status: 'queued',
            audioFile: req.file.filename,
            audioPath: audioPath,
            metadata: metadata,
            startTime: Date.now(),
            progress: {
                step: 'upload',
                message: 'Fichier reçu'
            }
        });
        
        // Répondre immédiatement avec le job ID
        res.json({
            success: true,
            jobId: jobId,
            message: 'Contribution reçue, traitement en cours...',
            audioFile: req.file.filename
        });
        
        // Lancer le traitement en arrière-plan
        this.processAudioContribution(jobId).catch(error => {
            console.error('❌ Erreur traitement contribution:', error);
            const job = this.processingJobs.get(jobId);
            if (job) {
                job.status = 'error';
                job.error = error.message;
            }
        });
    }
    
    /* ===========================
       ARCHIVE
       =========================== */
    
    async getArchive() {
        try {
            const outputDir = path.join(this.projectRoot, 'output_mix_play');
            const files = await fs.readdir(outputDir);
            
            const archive = [];
            
            for (const file of files) {
                if (file.endsWith('_info.json')) {
                    try {
                        const infoPath = path.join(outputDir, file);
                        const content = await fs.readFile(infoPath, 'utf8');
                        const info = JSON.parse(content);
                        
                        const audioFile = file.replace('_info.json', '.mp3');
                        const audioPath = path.join(outputDir, audioFile);
                        
                        // Vérifier que le fichier audio existe
                        await fs.access(audioPath);
                        
                        archive.push({
                            phrase: info.phrase || info.generated_phrase || 'Phrase inconnue',
                            words: info.query ? info.query.split(' ') : [],
                            audioFile: `/audio/${audioFile}`,
                            timestamp: info.timestamp || Date.now(),
                            duration: info.duration || null
                        });
                    } catch (e) {
                        // Ignorer les fichiers corrompus
                    }
                }
            }
            
            // Trier par timestamp décroissant (plus récent en premier)
            return archive.sort((a, b) => b.timestamp - a.timestamp).slice(0, 20);
            
        } catch (error) {
            console.error('Erreur récupération archive:', error);
            return [];
        }
    }
    
    /* ===========================
       RECHERCHE DANS LES TRANSCRIPTIONS
       =========================== */
    
    async searchTranscriptions(query, limit = 10, offset = 0) {
        return new Promise((resolve, reject) => {
            const script = path.join(__dirname, 'search_transcriptions.py');
            
            const pythonArgs = [script, query, limit.toString(), offset.toString()];
            
            const python = spawn(this.pythonPath, pythonArgs, {
                cwd: this.projectRoot,
                env: { 
                    ...process.env, 
                    PYTHONPATH: this.projectRoot,
                    PYTHONIOENCODING: 'utf-8',
                    LANG: 'en_US.UTF-8'
                }
            });
            
            let output = '';
            let error = '';
            
            python.stdout.on('data', (data) => {
                output += data.toString('utf8');
            });
            
            python.stderr.on('data', (data) => {
                error += data.toString('utf8');
            });
            
            python.on('close', (code) => {
                if (code !== 0) {
                    console.error('❌ Erreur Python recherche:', error);
                    reject(new Error('Erreur lors de la recherche'));
                    return;
                }
                
                try {
                    // Parser le JSON de sortie
                    const result = JSON.parse(output.trim());
                    resolve(result);
                } catch (e) {
                    console.error('❌ Erreur parsing JSON recherche:', e, '\nOutput:', output);
                    reject(new Error('Erreur de parsing de la réponse de recherche'));
                }
            });
        });
    }
    
    async extractAudioSegment(audioPath, startTime, endTime) {
        return new Promise((resolve, reject) => {
            const script = path.join(__dirname, 'extract_audio_segment.py');
            
            const pythonArgs = [
                script,
                audioPath,
                startTime.toString(),
                endTime.toString()
            ];
            
            const python = spawn(this.pythonPath, pythonArgs, {
                cwd: this.projectRoot,
                env: { 
                    ...process.env, 
                    PYTHONPATH: this.projectRoot,
                    PYTHONIOENCODING: 'utf-8',
                    LANG: 'en_US.UTF-8'
                }
            });
            
            let output = '';
            let error = '';
            
            python.stdout.on('data', (data) => {
                output += data.toString('utf8');
            });
            
            python.stderr.on('data', (data) => {
                error += data.toString('utf8');
            });
            
            python.on('close', (code) => {
                if (code !== 0) {
                    console.error('❌ Erreur Python extraction audio:', error);
                    reject(new Error('Erreur lors de l\'extraction audio'));
                    return;
                }
                
                try {
                    const result = JSON.parse(output.trim());
                    resolve(result);
                } catch (e) {
                    console.error('❌ Erreur parsing JSON extraction:', e, '\nOutput:', output);
                    reject(new Error('Erreur de parsing de la réponse d\'extraction'));
                }
            });
        });
    }
    
    /* ===========================
       DÉMARRAGE SERVEUR
       =========================== */
    
    start() {
        // Vérifier si les certificats SSL existent
        const sslKeyPath = path.join(__dirname, 'ssl', 'key.pem');
        const sslCertPath = path.join(__dirname, 'ssl', 'cert.pem');
        
        const useSSL = fsSync.existsSync(sslKeyPath) && fsSync.existsSync(sslCertPath);
        
        if (useSSL) {
            // Démarrer en HTTPS
            const sslOptions = {
                key: fsSync.readFileSync(sslKeyPath),
                cert: fsSync.readFileSync(sslCertPath)
            };
            
            https.createServer(sslOptions, this.app).listen(this.port, '0.0.0.0', () => {
                console.log(`🎭 Interface poétique démarrée (HTTPS):`);
                console.log(`   → https://localhost:${this.port}`);
                
                // Afficher l'IP locale pour accès mobile
                const { networkInterfaces } = require('os');
                const nets = networkInterfaces();
                for (const name of Object.keys(nets)) {
                    for (const net of nets[name]) {
                        // Afficher IPv4 non-interne
                        if (net.family === 'IPv4' && !net.internal) {
                            console.log(`   → https://${net.address}:${this.port} (réseau local)`);
                        }
                    }
                }
                
                console.log('');
                console.log('📱 Pour iOS: acceptez le certificat auto-signé lors de la première connexion');
                console.log('🎪 Prêt pour la performance live');
            });
        } else {
            // Démarrer en HTTP (fallback)
            this.app.listen(this.port, '0.0.0.0', () => {
                console.log(`🎭 Interface poétique démarrée (HTTP):`);
                console.log(`   → http://localhost:${this.port}`);
                console.log(`   → http://0.0.0.0:${this.port} (réseau)`);
                console.log('');
                console.log('⚠️  Mode HTTP: le microphone ne fonctionnera pas sur iOS');
                console.log('💡 Générez des certificats SSL pour activer HTTPS');
                console.log('🎪 Prêt pour la performance live');
            });
        }
        
        // Gestion propre de l'arrêt
        process.on('SIGINT', () => {
            console.log('\\n🎭 Arrêt du serveur poétique...');
            process.exit(0);
        });
    }
}

/* ===========================
   DÉMARRAGE
   =========================== */

if (require.main === module) {
    const server = new PoeticServer();
    server.start();
}

module.exports = PoeticServer;