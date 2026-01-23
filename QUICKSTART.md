# Guide de Démarrage Rapide 🚀

## Lancement Simple

Pour utiliser l'interface interactive (recommandé) :

```bash
./launch.sh
```

Ou si le script bash ne fonctionne pas :

```bash
source .venv/bin/activate
python launcher_interactif.py
```

## Workflow Typique

### Option 1: Interface Interactive (Recommandée)
1. Lancez `./launch.sh`
2. Choisissez "4. Workflow complet"
3. Sélectionnez votre fichier audio
4. Configurez les options
5. Laissez le système travailler !

### Option 2: Étapes Manuelles
1. **Transcription** : `python transcribe_audio.py --input audio/fichier.mp3 --reconstruct-sentences`
2. **Analyse** : `python analyze_love.py --input output_transcription/fichier_complete.json`

## Fichiers de Sortie

- **output_transcription/** : Transcriptions brutes et reconstruites
- **output_semantic/** : Analyses sémantiques des types d'amour
- **output_sentences/** : Phrases reconstruites uniquement

## Types d'Analyse d'Amour Détectés

L'analyse sémantique identifie 7 types d'amour :
- **Romantique** : Amour passionnel, sentiment amoureux
- **Familial** : Amour familial, liens de sang
- **Amical** : Amitié profonde, affection
- **Spirituel** : Amour divin, connexion spirituelle
- **Érotique** : Désir physique, sensualité
- **Narcissique** : Amour de soi, ego
- **Platonique** : Amour intellectuel, sans dimension physique

## Conseils d'Optimisation

- **Modèle Whisper** : `medium` pour l'équilibre, `large` pour la précision
- **Reconstruction** : Toujours recommandée pour l'analyse sémantique
- **Formats** : JSON pour les données complètes, CSV pour les tableaux
- **Threshold** : 0.15 par défaut, diminuer pour plus de sensibilité

## Dépannage

### Erreur d'environnement
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Erreur de mémoire
Utilisez un modèle plus petit : `small` ou `base`

### Fichiers non trouvés
Vérifiez que vos fichiers audio sont dans le dossier `audio/`