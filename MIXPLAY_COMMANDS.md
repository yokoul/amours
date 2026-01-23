# 🎵 Mix-Play Audio Generator - Commandes Disponibles

## 📋 **Commandes de Test Direct**

### 🎯 Test Phrase Simple (Recommandé)
```bash
# Activation environnement
source /Users/yan/synoul415/devel/texts_AA/.venv/bin/activate

# Test d'une phrase (génère et lit automatiquement)
python examples/test_phrase.py "ta phrase ici"

# Exemples testés
python examples/test_phrase.py "bonjour comment allez vous aujourd hui"
python examples/test_phrase.py "sans aucun amour la vie est triste"
python examples/test_phrase.py "avec tout mon amour je te dis bonjour"
python examples/test_phrase.py "la vie est belle comme une chanson"
python examples/test_phrase.py "je t aime de tout mon coeur"
```

### 🎨 Test Audio Avancé (6 variantes avec effets)
```bash
python examples/test_advanced_audio.py
# Génère 6 versions avec différents effets :
# - Standard, Artistique, Seamless
# - Tempo ralenti (0.7x), très lent (0.5x), accéléré (1.3x)
```

### 🎛️ Générateur Interactif (Menu complet)
```bash
python examples/interactive_generator.py
# Menu avec :
# 1. Composition personnalisée
# 2. Test phrases prédéfinies 
# 3. Explorateur vocabulaire
# 4. Génération effets avancés
# 5. Comparaison avec/sans diversification
# 6. Analyse phrases multiples
```

### 🔄 Génération Batch (Tests massifs)
```bash
# Version complète (64 fichiers : 16 phrases × 4 configs)
python examples/batch_generator.py

# Version rapide (3 phrases seulement)
python examples/batch_generator.py quick
```

## 🔍 **Commandes d'Analyse**

### 📚 Exploration du Vocabulaire
```bash
python examples/vocabulary_explorer.py
# Mode interactif pour chercher des mots disponibles

python examples/vocabulary_explorer.py "motif"
# Recherche mots contenant "motif"
```

### 🧪 Test de Diversification
```bash
python examples/test_source_diversity.py
# Analyse la diversité des sources avec mots répétés
```

### 🔍 Diagnostic Recherche
```bash
python examples/diagnose_search.py
# Analyse pourquoi certains mots ne sont pas trouvés
```

## 📊 **Fonctionnalités Implémentées**

### ✨ Diversification des Sources
- **Algorithme intelligent** : Privilégie sources moins utilisées
- **Tracking en temps réel** : Évite répétition mêmes extraits
- **Score de diversité** : 90%+ vs 60% mode standard
- **Indicateurs visuels** : ✨ nouvelle source, 🔄 source réutilisée

### 🎵 Modes Audio
- **Standard** : Transitions classiques
- **Artistique** : Fondus longs (150ms), effet rêveur
- **Seamless** : Fondus courts (15ms), plus naturel
- **Tempo** : 0.5x à 1.3x avec préservation pitch

### 🎯 Algorithme de Recherche Amélioré
- **Correspondance exacte** prioritaire
- **Recherche morphologique** (préfixes/suffixes)
- **Seuil strict** (0.9) pour éviter fausses correspondances
- **Nettoyage intelligent** des mots (accents, ponctuation)

## 📁 **Structure des Fichiers**

```
examples/
├── test_phrase.py              # ⭐ Test direct phrase
├── test_advanced_audio.py      # 🎨 Effets audio
├── interactive_generator.py    # 🎛️ Menu complet
├── batch_generator.py          # 🔄 Tests massifs
├── vocabulary_explorer.py      # 📚 Exploration mots
├── test_source_diversity.py    # 🧪 Analyse diversité
└── diagnose_search.py          # 🔍 Diagnostic

src/
└── mix_player.py               # 🎵 Moteur principal

output_mix_play/                # 🎧 Fichiers générés
```

## 🎧 **Notes sur la Qualité Audio**

### ⚠️ Problèmes Identifiés
- **Recherche approximative** : "vois" → "voisin", "bonheur" → "bonjour"
- **Qualité variable** selon sources originales
- **Transitions** parfois artificielles malgré fondus
- **Tempo changes** peuvent créer artefacts

### ✅ Points Forts
- **Diversification sources** fonctionne (différentes voix)
- **Indexation précise** des timecodes
- **Algorithme de recherche** plus strict
- **Génération rapide** et automatique

## 🚀 **Pour Reprendre Plus Tard**

1. **Test rapide** : `python examples/test_phrase.py "phrase test"`
2. **Vérification vocabulary** : `python examples/vocabulary_explorer.py`
3. **Analyse problèmes** : `python examples/diagnose_search.py`
4. **Tests comparison** : Menu interactif option 5

---

*Système en pause - Fonctionnalités de base opérationnelles mais qualité audio à affiner*