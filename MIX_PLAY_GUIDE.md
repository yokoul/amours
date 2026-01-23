# Mix-Play - Compositeur de Phrases Audio

Le système **Mix-Play** permet de composer de nouvelles phrases en utilisant les mots extraits des enregistrements audio transcrits, avec leurs timecodes précis. Cette fonctionnalité artistique transforme vos transcriptions en matériel créatif pour générer des phrases personnalisées avec les voix originales.

## 🎯 Concept

L'idée est de pouvoir écrire une phrase comme "*Avec tous l'amour du monde le bonheur nous rempli de la vie elle-même*" et de composer automatiquement cette phrase en sélectionnant les mots dans les différents enregistrements audio pour créer un rendu vocal mélangé et harmonieux.

## 🚀 Fonctionnalités

- **Indexation intelligente** : Tous les mots des transcriptions sont indexés avec leurs métadonnées (timecodes, intervenant, confiance)
- **Recherche flexible** : Recherche de mots avec normalisation des accents et gestion de la ponctuation
- **Stratégies multiples** : Mots individuels OU groupes de mots (chunks) pour plus de naturel
- **Génération audio optimisée** : Padding contextuel, normalisation, transitions douces
- **Comparaison interactive** : Test de différentes approches avec écoute comparative

## 📁 Structure des fichiers

```
src/
├── mix_player.py              # Module principal Mix-Play (mots individuels)
examples/
├── chunk_mix_player.py        # Système par groupes de mots (chunks)
├── test_audio_quality.py      # Tests de qualité audio
├── smart_mix_test.py          # Sélection contextuelle intelligente
final_mix_play.py              # Interface finale comparative
mix_play_interactive.py        # Interface interactive originale
vocabulary_explorer.py         # Explorateur de vocabulaire
output_mix_play/              # Fichiers générés (audio + infos)
```

## 🎮 Utilisation

### Interface Finale (Recommandée) 🆕

```bash
python final_mix_play.py
```

Cette interface propose :
- **Comparaison des stratégies** : Mots individuels vs chunks vs sélection intelligente
- **Analyse automatique** : Recommandation de la meilleure approche
- **Écoute comparative** : Test direct des différentes versions
- **Phrases prédéfinies** : Tests rapides avec des exemples optimisés

### Autres Interfaces Spécialisées

```bash
# Interface interactive complète
python mix_play_interactive.py

# Explorateur de vocabulaire
python vocabulary_explorer.py

# Tests de qualité audio
python examples/test_audio_quality.py
```

## ⚙️ Stratégies de Composition

### 1. Mots Individuels 🔤
- **Principe** : Sélection mot par mot dans les transcriptions
- **Avantages** : Flexibilité maximale, couverture étendue
- **Inconvénients** : Transitions parfois artificielles
- **Paramètres** : `word_padding` (0.1-0.3s), `crossfade_duration` (30-100ms)

### 2. Groupes de Mots (Chunks) 🧩 *NOUVEAU*
- **Principe** : Extraction de groupes de 2-5 mots consécutifs
- **Avantages** : Naturel vocal préservé, transitions fluides
- **Inconvénients** : Moins de flexibilité, couverture variable
- **Paramètres** : `chunk_padding` (0.1-0.2s), `gap_duration` (0.1-0.2s)

### 3. Sélection Contextuelle 🧠 *NOUVEAU*
- **Principe** : Privilégie la cohérence temporelle et les mêmes locuteurs
- **Avantages** : Cohérence vocale, qualité optimisée
- **Inconvénients** : Traitement plus lent
- **Paramètres** : `max_time_gap` (10s), `same_speaker_bonus` (0.1)

## 📊 Améliorations de Qualité Audio 🆕

### Optimisations Implementées
- **Padding contextuel** : 0.1-0.3s autour de chaque segment
- **Normalisation intelligente** : Volume équilibré entre segments
- **Transitions douces** : Fade-in/out automatiques
- **Détection de clics** : Élimination des artefacts audio
- **Crossfade adaptatif** : Fondu entre segments similaires

### Paramètres Ajustables
```python
generate_mixed_audio(
    word_padding=0.2,        # Contexte autour des mots
    gap_duration=0.2,        # Silence entre éléments
    crossfade_duration=50,   # Fondu entre segments
    normalize_volume=True    # Normalisation automatique
)
```

## 💡 Conseils d'Utilisation Mis à Jour

### Pour de Meilleurs Résultats

1. **Stratégie recommandée** : Commencez par les chunks pour un rendu naturel
2. **Phrases courtes** : 3-6 mots donnent les meilleurs résultats
3. **Mots courants** : Utilisez le vocabulaire disponible (voir `vocabulary_explorer.py`)
4. **Test comparatif** : Utilisez `final_mix_play.py` pour comparer les approches
5. **Ajustement audio** : Expérimentez avec les paramètres de padding et gap

### Stratégies Selon le Contexte

- **Prose narrative** : Privilégier les chunks (2-4 mots)
- **Expressions courtes** : Mots individuels avec haute confiance
- **Cohérence vocale** : Sélection contextuelle avec même locuteur
- **Créativité maximale** : Mélange de toutes les stratégies

## 🎵 Formats de Sortie

### Fichiers Audio (.mp3)
- Format MP3, 192 kbps
- Mixage optimisé avec normalisation
- Durées typiques : 1-5 secondes par phrase courte

### Comparaisons Automatiques 🆕
L'interface finale génère automatiquement plusieurs versions :
- `compare_words_hq_*` : Mots individuels haute qualité
- `compare_words_max_*` : Mots individuels couverture maximale  
- `compare_chunks_*` : Version par groupes de mots

## 🔧 Performances et Statistiques

### Résultats Typiques
- **Mots indexés** : ~8,300 mots depuis 3 enregistrements
- **Chunks extraits** : ~21,000 groupes de 2-4 mots
- **Temps de traitement** : 2-5 secondes par phrase
- **Taux de succès** : 80-95% selon la complexité

### Optimisations
- Cache audio automatique
- Index de recherche optimisé
- Traitement parallèle des stratégies

## 🐛 Résolution des Problèmes Audio 🆕

### Qualité Audio Médiocre
- **Solution** : Augmenter `word_padding` à 0.2-0.3s
- **Alternative** : Utiliser la stratégie chunks
- **Paramètres** : Réduire `crossfade_duration` si artefacts

### Transitions Trop Abruptes  
- **Solution** : Augmenter `crossfade_duration` à 80-100ms
- **Alternative** : Stratégie contextuelle avec même locuteur
- **Paramètres** : `normalize_volume=True` obligatoire

### Mots Parlés Trop Vite
- **Solution** : Utiliser les chunks qui préservent le rythme naturel
- **Alternative** : Sélectionner manuellement des passages plus lents
- **Paramètres** : Augmenter `gap_duration` à 0.3-0.5s

## 🌟 Évolutions et Améliorations 🆕

### Récemment Ajouté
- ✅ Système de chunks pour composition naturelle
- ✅ Sélection contextuelle intelligente  
- ✅ Interface comparative avec écoute directe
- ✅ Optimisations audio avancées (padding, normalisation)
- ✅ Tests de qualité automatisés

### Évolutions Futures
- Support de phrases avec plusieurs langues
- Analyse des émotions pour sélectionner le ton approprié
- Interface graphique avec visualisation des formes d'onde
- API REST pour intégration avec TouchDesigner
- Export vers formats professionnels (WAV 48kHz, stems séparés)

## 🎯 Cas d'Usage Artistiques

### Testés avec Succès
- **Messages personnalisés** : "avec tout mon amour" (chunks recommandés)
- **Poésie générative** : Assemblage créatif de fragments poétiques
- **Narration interactive** : Récits composés à la demande
- **Art sonore** : Matériau pour installations et performances

### Recommandations par Genre
- **Intimiste** : Privilégier un seul locuteur, chunks courts
- **Expérimental** : Mélanger les voix, mots individuels
- **Narratif** : Chunks de 3-4 mots, transitions douces
- **Rythmé** : Mots individuels, gaps réguliers

---

*Le système Mix-Play a évolué vers une approche multi-stratégies qui s'adapte au contexte et aux préférences artistiques, offrant un contrôle fin sur la qualité et le naturel du rendu vocal.*

## 🎮 Utilisation

### Interface Interactive (Recommandée)

```bash
python mix_play_interactive.py
```

Cette interface propose :
- Composition guidée de phrases
- Prévisualisation des correspondances
- Configuration des paramètres audio
- Génération automatique des fichiers

### Explorateur de Vocabulaire

```bash
python vocabulary_explorer.py
```

Utile pour :
- Analyser la faisabilité d'une phrase
- Trouver des mots similaires
- Découvrir des phrases optimisées

### Utilisation Programmatique

```python
from src.mix_player import MixPlayer

# Initialiser
mix_player = MixPlayer()
mix_player.load_transcriptions()

# Composer une phrase
composed = mix_player.compose_sentence(
    words=["avec", "tout", "mon", "amour"],
    min_confidence=0.7
)

# Générer l'audio
audio_file = mix_player.generate_mixed_audio(
    composed,
    "output_mix_play/ma_phrase.mp3"
)
```

## ⚙️ Configuration

### Paramètres de Recherche

- **`min_confidence`** : Confiance minimum (0.0 à 1.0, défaut: 0.5)
- **`preferred_speakers`** : Liste des intervenants préférés
- **`max_results`** : Nombre maximum de résultats par recherche

### Paramètres Audio

- **`gap_duration`** : Silence entre les mots (secondes, défaut: 0.3)
- **`crossfade_duration`** : Fondu entre segments (ms, défaut: 50)

## 📊 Analyse et Statistiques

Le système fournit des statistiques détaillées :
- Nombre total de mots indexés
- Distribution par intervenant et fichier
- Mots les plus fréquents
- Confiance moyenne des transcriptions

## 💡 Conseils d'Utilisation

### Pour de Meilleurs Résultats

1. **Utilisez des mots courants** : Les mots fréquents ont plus de choix d'intervenants
2. **Testez des variantes** : Essayez singulier/pluriel, masculin/féminin
3. **Ajustez la confiance** : Réduisez le seuil si peu de mots sont trouvés
4. **Explorez le vocabulaire** : Utilisez `vocabulary_explorer.py` pour découvrir les mots disponibles

### Stratégies de Composition

- **Haute qualité** : Confiance > 70%, moins de mots mais meilleure qualité audio
- **Maximum de mots** : Confiance > 40%, plus de mots mais qualité variable
- **Intervenant unique** : Utiliser `preferred_speakers` pour une voix cohérente

## 🎵 Formats de Sortie

### Fichier Audio (.mp3)
- Format MP3, 192 kbps
- Mixage automatique des différents segments
- Crossfade et espacement configurables

### Fichier d'Information (.json)
```json
{
  "metadata": {
    "text": "avec tout mon amour",
    "total_duration": 2.45,
    "speakers_used": ["Intervenant_1", "Intervenant_2"],
    "files_used": ["fichier1.mp3", "fichier2.mp3"],
    "words_count": 4
  },
  "words": [
    {
      "word": " avec",
      "start": 15.2,
      "end": 15.6,
      "confidence": 0.99,
      "speaker": "Intervenant_1",
      "file_name": "transcription1.mp3"
    }
  ]
}
```

## 🔧 Dépendances

Le système utilise les mêmes dépendances que le projet principal :
- `whisper` (transcription)
- `pydub` (traitement audio)
- `pathlib` (gestion des fichiers)
- `difflib` (recherche floue)

## 🎨 Exemples Créatifs

### Phrases Testées avec Succès
- "avec tout mon amour du monde"
- "le bonheur de la vie nous donne"
- "tous les moments de bonheur"
- "dans la vie il y a l'amour"

### Cas d'Usage Artistiques
- **Poésie générative** : Créer des vers à partir des transcriptions
- **Messages personnalisés** : Composer des messages avec les voix des proches
- **Art sonore** : Utiliser les compositions comme matériel créatif
- **Installation interactive** : Système en temps réel pour performances

## 🐛 Dépannage

### Mots Non Trouvés
- Vérifiez l'orthographe
- Essayez des variantes (accent, pluriel)
- Utilisez `vocabulary_explorer.py` pour trouver des alternatives
- Réduisez le seuil de confiance

### Qualité Audio
- Augmentez `min_confidence` pour une meilleure qualité
- Ajustez `crossfade_duration` pour des transitions plus douces
- Modifiez `gap_duration` pour l'espacement entre mots

### Performances
- Les fichiers audio sont mis en cache automatiquement
- Le premier chargement peut prendre quelques secondes
- L'indexation est faite une seule fois au démarrage

## 🌟 Évolutions Futures

- Support de phrases avec plusieurs langues
- Analyse des émotions pour sélectionner le ton approprié
- Interface graphique pour visualiser les formes d'onde
- API REST pour intégration avec d'autres outils (comme TouchDesigner)
- Export vers d'autres formats audio (WAV, FLAC)

---

*Le système Mix-Play est conçu comme une extension artistique du projet de transcription, ouvrant de nouvelles possibilités créatives avec les données audio existantes.*