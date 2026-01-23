# Guide de Contribution - Amours ❤️

Merci de votre intérêt pour contribuer au projet Amours ! Ce guide vous aidera à contribuer efficacement.

## 🚀 Premiers Pas

### Prérequis
- Python 3.8+
- Git
- Compte GitHub

### Configuration de l'environnement de développement

```bash
# 1. Fork le projet sur GitHub
# 2. Cloner votre fork
git clone https://github.com/VOTRE-USERNAME/amours.git
cd amours

# 3. Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou .venv\Scripts\activate  # Windows

# 4. Installer les dépendances
pip install -r requirements.txt

# 5. Installer les dépendances de développement
pip install pytest black flake8

# 6. Configurer le remote upstream
git remote add upstream https://github.com/OWNER/amours.git
```

## 🔄 Workflow de Contribution

### 1. Créer une branche pour votre fonctionnalité

```bash
git checkout -b feature/nom-de-votre-fonctionnalite
```

### 2. Faire vos modifications

- Suivez les conventions de code du projet
- Ajoutez des tests si nécessaire
- Mettez à jour la documentation

### 3. Tests et validation

```bash
# Formatter le code
black .

# Vérifier le style
flake8 .

# Lancer les tests
pytest
```

### 4. Commit et push

```bash
git add .
git commit -m "feat: description claire de votre ajout"
git push origin feature/nom-de-votre-fonctionnalite
```

### 5. Créer une Pull Request

1. Allez sur GitHub
2. Cliquez sur "New Pull Request"
3. Décrivez clairement vos changements
4. Attendez la review

## 📝 Conventions de Code

### Style Python
- Utilisez **Black** pour le formatting automatique
- Suivez **PEP 8**
- Longueur de ligne : 88 caractères (Black default)

### Convention de nommage
```python
# Classes : PascalCase
class LoveAnalyzer:
    pass

# Fonctions et variables : snake_case
def analyze_love_types():
    semantic_score = 0.5

# Constantes : UPPER_SNAKE_CASE
DEFAULT_THRESHOLD = 0.15
```

### Docstrings
Utilisez le format Google :

```python
def analyze_transcription(self, data: Dict, threshold: float = 0.15) -> Dict:
    """
    Analyse sémantique d'une transcription pour détecter les types d'amour.
    
    Args:
        data: Données de transcription au format JSON
        threshold: Seuil de détection (0.0-1.0)
        
    Returns:
        Résultats d'analyse avec scores et classifications
        
    Raises:
        ValueError: Si les données sont invalides
    """
```

## 🧪 Tests

### Structure des tests
```
tests/
├── test_transcriber.py
├── test_love_analyzer.py
├── test_sentence_reconstructor.py
└── fixtures/
    ├── sample_audio.mp3
    └── sample_transcription.json
```

### Écriture de tests
```python
import pytest
from src.love_analyzer import LoveAnalyzer

class TestLoveAnalyzer:
    def setup_method(self):
        self.analyzer = LoveAnalyzer()
    
    def test_analyze_romantic_content(self):
        # Arrange
        text = "Je t'aime de tout mon cœur"
        
        # Act
        result = self.analyzer.analyze_text(text)
        
        # Assert
        assert "romantique" in result["detected_types"]
        assert result["scores"]["romantique"] > 0.5
```

## 🎯 Types de Contributions

### 🐛 Correction de bugs
- Décrivez le problème clairement
- Incluez les étapes de reproduction
- Proposez une solution testée

### ✨ Nouvelles fonctionnalités
- Discutez d'abord dans une Issue
- Implémentez avec des tests
- Documentez l'utilisation

### 📚 Documentation
- Amélioration du README
- Ajout d'exemples
- Correction de typos

### 🎨 Modèles et analyses
- Nouveaux types d'amour à détecter
- Amélioration des modèles existants
- Optimisation des performances

## 📋 Checklist avant Pull Request

- [ ] Code formatté avec Black
- [ ] Tests passent (`pytest`)
- [ ] Style respecté (`flake8`)
- [ ] Documentation mise à jour
- [ ] Exemples ajoutés si nécessaire
- [ ] Changements décrits dans la PR

## 🆘 Besoin d'aide ?

- **Issues** : Pour rapporter des bugs ou proposer des fonctionnalités
- **Discussions** : Pour les questions générales
- **Discord/Slack** : Pour les discussions en temps réel (si applicable)

## 🏷️ Convention de commit

Utilisez [Conventional Commits](https://www.conventionalcommits.org/) :

```
feat: ajouter détection type d'amour spirituel
fix: corriger erreur parsing audio MP3
docs: mettre à jour guide d'installation
style: formater code avec Black
refactor: simplifier algorithme de clustering
test: ajouter tests pour sentence reconstructor
```

## 🎉 Reconnaissance

Tous les contributeurs seront ajoutés dans :
- Section "Contributors" du README
- Fichier AUTHORS.md
- Mentions dans les release notes

Merci de contribuer à rendre l'analyse des sentiments amoureux plus accessible ! ❤️