# 🎙️ Guide d'Enregistrement Audio - Contributions Usagers

## Vue d'ensemble

Le système d'enregistrement audio permet aux usagers de contribuer directement depuis l'interface web. Chaque enregistrement est automatiquement transcrit et analysé sémantiquement.

## Architecture du Système

### 1. Frontend (Interface Web)

**Composants créés:**
- `audio-recorder.js` - Module de capture audio (MediaRecorder API)
- `recording-interface.js` - Interface utilisateur d'enregistrement
- `recording-interface.css` - Styles de l'interface

**Fonctionnalités:**
- ✅ Enregistrement audio avec contrôles (pause/reprendre)
- ✅ Prévisualisation avant envoi
- ✅ Upload vers le serveur
- ✅ Suivi du traitement en temps réel
- ✅ Feedback visuel de l'état de traitement

### 2. Backend (Serveur Node.js)

**API Routes ajoutées:**
- `POST /api/upload-contribution` - Upload fichier audio
- `GET /api/processing-status/:jobId` - Vérifier statut de traitement

**Pipeline de traitement:**
1. Upload → Sauvegarde dans `audio/contributions/`
2. Transcription → Appel de `src/main_with_speakers.py`
3. Analyse sémantique → Appel de `analyze_love.py`

### 3. Traitement Python

**Scripts utilisés:**
- `src/main_with_speakers.py` - Transcription avec détection d'intervenants
- `analyze_love.py` - Analyse sémantique des types d'amour

**Dossiers de sortie:**
- `audio/contributions/` - Enregistrements bruts
- `output_transcription/` - Fichiers JSON de transcription
- `output_semantic/` - Analyses sémantiques

## Utilisation

### Pour les Usagers

1. **Ouvrir l'interface d'enregistrement**
   - Cliquer sur le bouton 🎙️ dans la navigation
   - Autoriser l'accès au microphone

2. **Enregistrer**
   - Cliquer sur "Commencer l'enregistrement"
   - Parler sur le thème de l'amour
   - Utiliser les contrôles: pause/reprendre/terminer

3. **Prévisualiser**
   - Écouter l'enregistrement
   - Choisir: recommencer ou envoyer

4. **Traitement automatique**
   - Le système transcrit l'audio
   - Analyse sémantique automatique
   - Notification de succès

### États de l'Interface

```
ready → recording → preview → uploading → processing → success/error
```

**États détaillés:**
- `ready` - Prêt à enregistrer
- `recording` - Enregistrement en cours
- `preview` - Prévisualisation audio
- `uploading` - Envoi au serveur
- `processing` - Traitement en cours (transcription + analyse)
- `success` - Traitement terminé avec succès
- `error` - Erreur lors du processus

## Formats Audio Supportés

- WebM (préféré, codec Opus)
- OGG (codec Opus)
- MP4
- WAV
- MP3

Le système détecte automatiquement le meilleur format supporté par le navigateur.

## Configuration

### Serveur Node.js

```javascript
// Dans poetic-server.js
this.processingJobs = new Map(); // Stockage des jobs de traitement

// Paramètres upload
limits: { fileSize: 50 * 1024 * 1024 } // 50 MB max
```

### Transcription Python

```bash
# Modèle utilisé: medium (équilibré)
# Options:
--model medium
--output-dir output_transcription
--reconstruct-sentences
```

### Analyse Sémantique

```bash
# Seuil de détection: 0.15
--output-dir output_semantic
--threshold 0.15
```

## Workflow de Traitement

### 1. Upload (côté serveur)

```javascript
POST /api/upload-contribution
- Reçoit fichier audio via multer
- Génère nom unique avec timestamp
- Sauvegarde dans audio/contributions/
- Crée job ID pour tracking
- Retourne job ID immédiatement
```

### 2. Transcription (Python)

```bash
python src/main_with_speakers.py \
  audio/contributions/contribution_xxx.webm \
  --model medium \
  --output-dir output_transcription \
  --reconstruct-sentences
```

**Sortie:**
- `contribution_xxx_with_speakers_complete.json`

### 3. Analyse Sémantique (Python)

```bash
python analyze_love.py \
  output_transcription/contribution_xxx_with_speakers_complete.json \
  --output-dir output_semantic \
  --threshold 0.15
```

**Sortie:**
- `contribution_xxx_with_speakers_complete_love_analysis.json`
- `contribution_xxx_with_speakers_complete_love_summary.txt`

### 4. Suivi du Statut

```javascript
GET /api/processing-status/:jobId
// Retourne:
{
  jobId: "xxx",
  status: "processing", // queued, processing, completed, error
  progress: {
    step: "transcription", // upload, transcription, semantic, completed
    message: "Transcription audio en cours..."
  },
  audioFile: "contribution_xxx.webm"
}
```

## Structure des Fichiers

```
web-interface/
├── public/
│   ├── audio-recorder.js          # Module capture audio
│   ├── recording-interface.js     # Interface UI
│   ├── recording-interface.css    # Styles
│   └── poetic-interface.html      # Page principale (modifiée)
└── poetic-server.js               # Serveur (modifié)

audio/
└── contributions/                  # Enregistrements usagers
    └── contribution_*.webm

output_transcription/
└── contribution_*_with_speakers_complete.json

output_semantic/
├── contribution_*_love_analysis.json
└── contribution_*_love_summary.txt
```

## Intégration dans l'Interface Existante

### HTML ajouté

```html
<!-- Bouton dans la navigation -->
<button class="nav-btn" data-action="record">
    <span>🎙️</span>
</button>

<!-- Styles -->
<link rel="stylesheet" href="recording-interface.css">

<!-- Scripts -->
<script src="audio-recorder.js"></script>
<script src="recording-interface.js"></script>
```

### JavaScript ajouté

```javascript
// Dans poetic-interface.js
openRecordingInterface() {
    if (!window.recordingInterface) {
        window.recordingInterface = new RecordingInterface();
    }
    window.recordingInterface.open();
}
```

## Gestion des Erreurs

### Erreurs Possibles

1. **Microphone non accessible**
   - Message: "Impossible d'accéder au microphone"
   - Solution: Vérifier permissions navigateur

2. **Upload échoué**
   - Message: "Erreur lors de l'envoi"
   - Solution: Vérifier connexion réseau

3. **Transcription échouée**
   - Cause: Fichier audio corrompu ou format non supporté
   - Log serveur avec détails

4. **Analyse échouée**
   - Cause: Fichier JSON de transcription invalide
   - Log serveur avec détails

### Logs

**Côté serveur:**
```
🎤 Nouvelle contribution reçue
📝 Transcription démarrée pour contribution_xxx.webm
❤️ Analyse sémantique démarrée
✅ Contribution traitée avec succès
```

## Performance

### Temps de Traitement Estimés

- Upload: ~2-5s (dépend connexion)
- Transcription: ~30s-2min (dépend durée audio)
- Analyse sémantique: ~5-15s

**Total moyen:** 1-3 minutes pour un enregistrement de 1-2 minutes

### Optimisations

- Traitement asynchrone (non-bloquant)
- Polling toutes les 5 secondes
- Timeout max: 10 minutes
- Compression audio automatique

## Sécurité

- ✅ Validation du type MIME
- ✅ Limite de taille: 50 MB
- ✅ Noms de fichiers uniques (crypto.randomBytes)
- ✅ Sanitisation des chemins
- ✅ Vérification des extensions

## Extension Future

### Fonctionnalités Possibles

1. **Métadonnées enrichies**
   - Nom du contributeur (optionnel)
   - Lieu d'enregistrement
   - Tags personnalisés

2. **Modération**
   - Validation manuelle avant ajout au corpus
   - Interface d'administration

3. **Qualité audio**
   - Détection de niveau sonore
   - Suppression automatique du bruit
   - Normalisation audio

4. **Statistiques**
   - Nombre de contributions
   - Durée totale enregistrée
   - Types d'amour les plus fréquents

## Dépannage

### Problème: Interface ne s'ouvre pas

```javascript
// Vérifier dans la console:
console.log(window.RecordingInterface); // Doit être défini
console.log(window.recordingInterface); // Instance après premier clic
```

### Problème: Statut de traitement non mis à jour

```javascript
// Vérifier le polling:
GET /api/processing-status/:jobId
// Doit retourner un objet JSON avec status et progress
```

### Problème: Transcription échoue

```bash
# Tester manuellement:
cd /Users/yan/synoul415/devel/texts_AA
source .venv/bin/activate
python src/main_with_speakers.py audio/contributions/contribution_xxx.webm --model medium
```

## Commandes Utiles

### Redémarrer le serveur

```bash
cd web-interface
node poetic-server.js
```

### Voir les contributions

```bash
ls -lh audio/contributions/
```

### Voir les transcriptions

```bash
ls -lh output_transcription/contribution_*
```

### Nettoyer les anciennes contributions

```bash
# Attention: supprime définitivement
rm audio/contributions/contribution_*
rm output_transcription/contribution_*
rm output_semantic/contribution_*
```

## Support

Pour toute question ou problème:
1. Vérifier les logs serveur
2. Vérifier la console navigateur (F12)
3. Tester le processus manuellement avec Python
4. Consulter ce guide

---

**Dernière mise à jour:** 26 janvier 2026
