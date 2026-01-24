const express = require('express');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const WebSocket = require('ws');
const cors = require('cors');

const app = express();
const PORT = 3000;

// Configuration pour serveur captif
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
// Route pour servir les fichiers audio générés
app.use('/audio', express.static(path.join(__dirname, 'public', 'audio')));

// WebSocket pour les mises à jour temps réel
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
    console.log('Nouveau client connecté');
    
    ws.on('message', (message) => {
        console.log('Message reçu:', message.toString());
    });
    
    ws.on('close', () => {
        console.log('Client déconnecté');
    });
});

// Fonction pour broadcaster aux clients WebSocket
function broadcast(data) {
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(data));
        }
    });
}

// Route principale - redirection captive
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API pour générer des phrases
app.post('/api/generate-phrase', async (req, res) => {
    try {
        const { words, count } = req.body;
        console.log(`Génération demandée: ${count} phrases avec mots:`, words);
        
        // Préparer les arguments pour phrase_montage.py
        const args = [count.toString(), ...words];
        
        // Lancer le script Python web-optimisé avec l'environnement virtuel
        const pythonPath = path.join(__dirname, '..', '.venv', 'bin', 'python');
        const scriptPath = path.join(__dirname, 'web_phrase_generator.py');
        const pythonProcess = spawn(pythonPath, [
            scriptPath,
            count.toString(),
            ...words
        ], {
            cwd: path.join(__dirname, '..'),
            env: { ...process.env, PYTHONIOENCODING: 'utf-8', LANG: 'en_US.UTF-8' },
            encoding: 'utf8'
        });
        
        let output = '';
        let error = '';
        
        pythonProcess.stdout.on('data', (data) => {
            const chunk = data.toString('utf8');
            output += chunk;
        });
        
        pythonProcess.stderr.on('data', (data) => {
            const chunk = data.toString('utf8');
            error += chunk;
        });
        
        pythonProcess.on('close', (code) => {
            if (code === 0) {
                // Nettoyer l'output dès le début pour éviter les problèmes d'emojis
                let cleanOutput = output.trim();
                
                // Supprimer tout ce qui précède le premier { et suit le dernier }
                const firstBrace = cleanOutput.indexOf('{');
                const lastBrace = cleanOutput.lastIndexOf('}');
                
                if (firstBrace !== -1 && lastBrace !== -1 && firstBrace < lastBrace) {
                    cleanOutput = cleanOutput.substring(firstBrace, lastBrace + 1);
                }
                
                try {
                    // Parser la réponse JSON du script Python
                    const result = JSON.parse(cleanOutput);
                    
                    // Debug: voir ce que contient result
                    console.log('🔍 Clés disponibles dans result:', Object.keys(result));
                    console.log('🔍 Audio base64 présent:', !!result.audio_base64);
                    console.log('🔍 Audio URL présent:', !!result.audio_url);
                    
                    // Créer une réponse sans l'audio base64 pour éviter les problèmes de parsing côté client
                    const safeResponse = {
                        success: true,
                        phrases: result.phrases || [],
                        keywords: result.keywords || words, // Utiliser 'words' du req.body
                        timestamp: result.timestamp,
                        duration_seconds: result.duration_seconds,
                        error: result.error,
                        has_audio: !!result.audio_base64
                    };
                    
                    // Gérer l'audio séparément
                    if (result.audio_base64) {
                        try {
                            const audioId = `audio_${result.timestamp}`;
                            const audioBuffer = Buffer.from(result.audio_base64, 'base64');
                            const audioPath = path.join(__dirname, 'public', 'audio', `${audioId}.mp3`);
                            
                            // Créer le dossier audio s'il n'existe pas
                            const audioDir = path.dirname(audioPath);
                            if (!fs.existsSync(audioDir)) {
                                fs.mkdirSync(audioDir, { recursive: true });
                            }
                            
                            fs.writeFileSync(audioPath, audioBuffer);
                            safeResponse.audio_url = `/audio/${audioId}.mp3`;
                            
                        } catch (audioError) {
                            console.warn('Erreur sauvegarde audio:', audioError);
                        }
                    } else if (result.audio_url) {
                        // Le script Python a déjà fourni une URL d'audio
                        console.log('📻 URL audio fournie par Python:', result.audio_url);
                        safeResponse.audio_url = result.audio_url;
                    } else if (result.audio_file) {
                        // Le script Python a fourni un chemin de fichier
                        console.log('📻 Fichier audio fourni par Python:', result.audio_file);
                        // Construire l'URL relative depuis le nom de fichier
                        const fileName = result.audio_file.split('/').pop();
                        safeResponse.audio_url = `/audio/${fileName}`;
                    }
                    
                    // Broadcaster le résultat à tous les clients APRÈS création audio
                    if (result.phrases && result.phrases.length > 0) {
                        const broadcastData = {
                            type: 'phrase_generated',
                            data: {
                                phrase: result.phrases[0],
                                keywords: words,
                                audio_url: safeResponse.audio_url, // Maintenant défini
                                duration: result.duration_seconds
                            }
                        };
                        
                        console.log('📡 Broadcasting avec audio_url:', safeResponse.audio_url);
                        broadcast(broadcastData);
                    }
                    
                    res.json(safeResponse);
                    
                } catch (parseError) {
                    console.error('❌ Erreur parsing JSON après nettoyage:', parseError);
                    console.error('📄 Output original (premiers 200 chars):', output.substring(0, 200));
                    console.error('📄 Output nettoyé (premiers 200 chars):', cleanOutput?.substring(0, 200) || 'N/A');
                    
                    res.status(500).json({
                        success: false,
                        error: 'Erreur de traitement de la réponse Python',
                        debug: {
                            outputLength: output.length,
                            hasJSON: output.includes('{') && output.includes('}'),
                            outputType: typeof output,
                            firstChars: output.substring(0, 100)
                        }
                    });
                }
            } else {
                console.error('Erreur Python:', error);
                res.status(500).json({
                    success: false,
                    error: error || "Erreur d'exécution Python"
                });
            }
        });
        
    } catch (error) {
        console.error('Erreur serveur:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// API pour obtenir des mots aléatoires du vocabulaire
app.get('/api/random-words/:count', (req, res) => {
    const count = parseInt(req.params.count) || 19;
    
    // Mots d'amour pour le damier (toujours "amour" + 19 aléatoires)
    const loveWords = [
        'passion', 'désir', 'tendresse', 'émotion', 'flamme',
        'cœur', 'âme', 'rêve', 'espoir', 'joie',
        'bonheur', 'extase', 'ivresse', 'folie', 'délire',
        'baiser', 'caresse', 'étreinte', 'regard', 'sourire',
        'larme', 'soupir', 'frisson', 'trouble', 'émoi',
        'séduction', 'charme', 'beauté', 'grâce', 'élégance',
        'étoile', 'lune', 'soleil', 'nuit', 'jour',
        'silence', 'murmure', 'chanson', 'mélodie', 'harmonie',
        'danse', 'valse', 'élan', 'envol', 'fuite'
    ];
    
    // Sélection aléatoire
    const shuffled = loveWords.sort(() => 0.5 - Math.random());
    const randomWords = shuffled.slice(0, count);
    
    res.json({
        words: ['amour', ...randomWords] // "amour" toujours en première position
    });
});

// Route catch-all pour serveur captif
app.get('*', (req, res) => {
    res.redirect('/');
});

app.listen(PORT, () => {
    console.log(`🎭 Serveur spectacle démarré sur http://localhost:${PORT}`);
    console.log(`📡 WebSocket sur ws://localhost:8080`);
    console.log(`🎵 Interface captive prête pour le public !`);
});