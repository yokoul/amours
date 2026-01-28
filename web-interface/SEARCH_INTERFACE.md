# Interface de Recherche dans les Transcriptions

## Vue d'ensemble

Cette fonctionnalité permet de rechercher des mots-clés ou des phrases dans toutes les transcriptions audio disponibles.

## Accès

L'interface de recherche est accessible à l'URL :
- **http://localhost:3000/search** (ou https si SSL configuré)

## Fonctionnalités

### 1. Recherche de mots-clés ou phrases
- Entrez n'importe quel mot ou phrase dans le champ de recherche
- La recherche est insensible à la casse
- Minimum 2 caractères requis

### 2. Affichage des résultats
Chaque résultat affiche :
- **Contexte** : 2-3 phrases avant et après le passage trouvé
- **Source** : Nom du fichier audio d'origine
- **Intervenant** : Badge indiquant le speaker
- **Timecodes** : Heure de début et de fin de l'extrait
- **Durée** : Durée totale de l'extrait

### 3. Lecture audio intégrée
Chaque résultat dispose d'un player minimaliste :
- **Bouton Play/Pause** : Lecture de l'extrait uniquement
- **Barre de progression** : Visualisation et navigation dans l'extrait
- **Timecode en direct** : Temps écoulé / durée totale

Le player charge automatiquement l'extrait exact du fichier audio source et le lit uniquement sur la plage de temps correspondante.

## Architecture technique

### Backend (Node.js)
- **Route** : `GET /api/search?q=<query>&max=<nombre>`
- **Script Python** : `search_transcriptions.py`
- **Serveur de fichiers audio** : `/audio-sources/` pour accéder aux fichiers sources

### Frontend
- **HTML** : `search-interface.html`
- **CSS** : `search-interface.css`
- **JavaScript** : `search-interface.js`

### Données
- **Source** : Fichiers JSON dans `output_transcription/`
- **Format** : `*_with_speakers_complete.json`

## Utilisation de l'API

### Exemple de requête
```bash
curl "http://localhost:3000/api/search?q=amour&max=20"
```

### Réponse
```json
{
  "success": true,
  "query": "amour",
  "total_results": 150,
  "returned_results": 20,
  "results": [
    {
      "source_file": "Adam par Laurent.mp3",
      "source_path": "/path/to/audio/Adam par Laurent.mp3",
      "transcription_file": "Adam par Laurent_with_speakers_complete",
      "segment_id": 5,
      "speaker": "Intervenant_2",
      "start_time": 45.2,
      "end_time": 62.8,
      "duration": 17.6,
      "matched_text": "Pour moi l'amour c'est...",
      "context_text": "... phrase avant. Pour moi l'amour c'est... phrase après ...",
      "context_segments": [...],
      "relevance_score": 0.95
    }
  ]
}
```

## Améliorations futures possibles

1. **Filtres avancés**
   - Par speaker
   - Par fichier source
   - Par durée

2. **Recherche sémantique**
   - Recherche par concepts (synonymes)
   - Recherche par type d'amour (éros, agapè, etc.)

3. **Export**
   - Télécharger les extraits audio trouvés
   - Exporter les résultats en PDF/CSV

4. **Partage**
   - Partager un extrait précis par lien
   - Créer des playlists de recherche
