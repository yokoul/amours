# Amours - Transcription Audio & Analyse Sémantique des Types d'Amour ❤️

Projet Python d'analyse sémantique avancée pour détecter et classifier les différents types d'amour dans des enregistrements audio français. Utilise l'intelligence artificielle (Whisper AI + sentence-transformers) pour une transcription précise et une analyse sémantique sophistiquée.

## 🚀 Fonctionnalités

- **🎵 Transcription audio intelligente** avec Whisper AI (OpenAI)
- **👥 Détection d'intervenants** par clustering acoustique
- **🔧 Reconstruction syntaxique** des phrases françaises complètes
- **🧠 Analyse sémantique des types d'amour** avec sentence-transformers
- **📊 Classification en 7 types d'amour** : romantique, familial, amical, spirituel, érotique, narcissique, platonique
- **🎯 Interface interactive** simplifiée pour tous les workflows
- **📄 Export multi-format** : JSON, CSV, SRT (sous-titres), mots avec timecodes

## 🛠️ Technologies

- **Python 3.8+**
- **Whisper AI** (OpenAI) - Transcription audio de pointe
- **sentence-transformers** - Analyse sémantique multilingue
- **scikit-learn** - Machine learning pour la classification
- **librosa** - Traitement audio avancé
- **PyDub** - Manipulation de fichiers audio

## 📦 Installation

```bash
# Cloner le projet
git clone https://github.com/yokoul/amours.git
cd amours

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Sur macOS/Linux
# ou sur Windows : .venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

## 🎯 Utilisation Rapide

### Interface Interactive (Recommandée)

```bash
# Lancement en une commande
./launch.sh

# Ou directement
python launcher_interactif.py
```

**Menu interactif :**
1. **🎵 Transcription simple** - Transcription avec options personnalisables
2. **🔧 Reconstruction de phrases** - Post-traitement sur fichiers existants  
3. **❤️ Analyse sémantique** - Analyse des types d'amour
4. **🔄 Workflow complet** - Pipeline automatique complet
5. **📁 Exploration de fichiers** - Vue d'ensemble des ressources

### Ligne de Commande

```bash
# Transcription complète avec analyse (recommandé)
python transcribe_audio.py --input audio/fichier.mp3 --reconstruct-sentences --with-semantic-analysis

# Étapes séparées
python transcribe_audio.py --input audio/fichier.mp3 --reconstruct-sentences
python analyze_love.py --input output_transcription/fichier_complete.json
```

## 🧠 Types d'Amour Détectés

Le système utilise un modèle sémantique avancé pour identifier 7 types d'amour avec précision :

| Type | Description | Exemples de détection |
|------|-------------|---------------------|
| **💕 Romantique** | Amour passionnel, sentiment amoureux | "je t'aime", "mon cœur", "passion" |
| **👨‍👩‍👧‍👦 Familial** | Amour familial, liens du sang | "ma famille", "mes parents", "fraternal" |
| **🤝 Amical** | Amitié profonde, affection platonique | "mon ami", "amitié sincère", "copain" |
| **🙏 Spirituel** | Amour divin, connexion transcendante | "divin", "sacré", "spiritualité" |
| **🔥 Érotique** | Désir physique, sensualité | "désir", "sensuel", "physique" |
| **🪞 Narcissique** | Amour de soi, ego | "moi-même", "supérieur", "admiration" |
| **📚 Platonique** | Amour intellectuel, sans dimension physique | "idéal", "intellectuel", "pur" |

## 📊 Exemples de Résultats

### Analyse Complète
```json
{
  "metadata": {
    "file": "interview_amour.mp3",
    "duration": 180.5,
    "speakers_detected": 2
  },
  "semantic_analysis": {
    "summary": {
      "detected_types": ["romantique", "familial", "amical"],
      "top_types": [
        {"type": "romantique", "score": 8.45},
        {"type": "familial", "score": 6.23}
      ]
    },
    "segments": [...]
  }
}
```

### Performance Typique
- **Précision transcription** : 95%+ (audio de bonne qualité)
- **Détection intervenants** : 85%+ de justesse
- **Analyse sémantique** : Classification fiable avec seuils ajustables
- **Vitesse** : ~2-3x temps réel (modèle medium)

## 🏗️ Architecture

```
amours/
├── src/                          # Code source principal
│   ├── transcriber.py           # Moteur de transcription Whisper
│   ├── love_analyzer.py         # Analyseur sémantique
│   ├── sentence_reconstructor.py # Reconstruction syntaxique
│   └── export.py               # Gestionnaire d'exports
├── audio/                       # Fichiers audio d'entrée
├── output_transcription/        # Transcriptions générées
├── output_semantic/            # Analyses sémantiques
├── launcher_interactif.py      # Interface utilisateur
└── examples/                   # Scripts d'exemple
```

```json
{
  "metadata": {
    "file": "audio.mp3",
    "duration": 120.5,
    "language": "fr",
    "model": "medium"
  },
  "transcription": {
    "text": "Bonjour, ceci est un test.",
    "segments": [
      {
        "start": 0.0,
        "end": 2.5,
        "text": "Bonjour, ceci est un test.",
        "words": [
          {"word": "Bonjour", "start": 0.0, "end": 0.8},
          {"word": "ceci", "start": 1.0, "end": 1.3},
          {"word": "est", "start": 1.4, "end": 1.6},
          {"word": "un", "start": 1.7, "end": 1.8},
          {"word": "test", "start": 1.9, "end": 2.5}
        ]
      }
    ]
  }
}
```

## 🤝 Contribution

Les contributions sont les bienvenues ! 

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/amelioration`)
3. Committez vos changements (`git commit -m 'Ajout fonctionnalité'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- **OpenAI** pour Whisper AI
- **Sentence Transformers** pour les modèles de similarité sémantique
- **Hugging Face** pour l'écosystème de modèles
- La communauté Python pour les outils de traitement audio

## 📞 Support

Pour toute question ou problème :
- Ouvrez une [Issue](https://github.com/yokoul/amours/issues)
- Consultez la [Documentation](docs/)
- Contactez les mainteneurs

---

*Développé avec ❤️ pour l'analyse sémantique des sentiments amoureux*