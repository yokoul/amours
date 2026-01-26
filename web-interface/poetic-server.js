/* ===========================
   SERVEUR POÉTIQUE
   Interface minimaliste pour performance live
   =========================== */

const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs').promises;
const cors = require('cors');

class PoeticServer {
    constructor() {
        this.app = express();
        this.port = 3000;
        
        // Chemins relatifs calculés automatiquement
        this.projectRoot = path.resolve(__dirname, '..');
        this.pythonPath = path.join(this.projectRoot, '.venv', 'bin', 'python');
        
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
        
        // Servir les fichiers audio générés
        this.app.use('/audio', express.static(path.join(this.projectRoot, 'output_mix_play')));
        
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
            'trahison', 'fidélité', 'odeur', 'couleur', 'chant'
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
       DÉMARRAGE SERVEUR
       =========================== */
    
    start() {
        this.app.listen(this.port, '0.0.0.0', () => {
            console.log(`🎭 Interface poétique démarrée:`);
            console.log(`   → http://localhost:${this.port}`);
            console.log(`   → http://0.0.0.0:${this.port} (réseau)`);
            console.log('');
            console.log('🎪 Prêt pour la performance live');
        });
        
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