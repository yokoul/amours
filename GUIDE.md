# Guide d'Utilisation - Transcription Audio avec Timecodes

## Démarrage rapide

1. **Préparer un fichier audio** :
   - Placez votre fichier audio dans le dossier `audio/`
   - Formats supportés : MP3, WAV, M4A, FLAC, OGG

2. **Transcription simple** :
   ```bash
   python src/main.py --input audio/votre_fichier.mp3 --output output/resultat.json
   ```

3. **Avec options avancées** :
   ```bash
   python src/main.py --input audio/discussion.wav --output output/transcription.json --model medium --language fr --format json
   ```

## Options disponibles

- `--model` : Modèle Whisper (tiny, base, small, medium, large)
- `--language` : Langue audio (fr pour français)
- `--format` : Format de sortie (json, csv)
- `--word-timestamps` : Timecodes au niveau des mots (activé par défaut)

## Formats d'export

### JSON complet
Structure complète avec métadonnées, segments et mots avec timecodes.

### CSV
Format tabulaire pour analyse avec Excel/Pandas.

### Format artistique
Optimisé pour l'exploitation créative avec timeline et vocabulaire.

### Sous-titres SRT
Pour intégration vidéo.

## Exemples d'utilisation artistique

- **Installation sonore** : Utiliser les timecodes pour synchroniser des éléments visuels
- **Performance** : Déclencher des événements sur des mots spécifiques
- **Analyse linguistique** : Étudier la fréquence et distribution des mots
- **Remixage audio** : Isoler et réorganiser des segments de parole