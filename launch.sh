#!/bin/bash

# Script de lancement rapide pour l'interface interactive
# Active l'environnement virtuel et lance le programme principal

echo "🚀 Lancement de l'interface interactive de transcription..."
echo "📁 Répertoire : $(pwd)"

# Vérifier que l'environnement virtuel existe
if [ ! -d ".venv" ]; then
    echo "❌ Environnement virtuel .venv non trouvé"
    echo "💡 Exécutez d'abord : python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activer l'environnement virtuel
source .venv/bin/activate

# Vérifier que Python est disponible
if ! python --version &> /dev/null; then
    echo "❌ Python non trouvé dans l'environnement virtuel"
    exit 1
fi

# Vérifier les dépendances critiques
echo "🔍 Vérification des dépendances..."
python -c "import whisper, sentence_transformers" 2>/dev/null || {
    echo "❌ Dépendances manquantes. Veuillez exécuter : pip install -r requirements.txt"
    exit 1
}

echo "✅ Environnement virtuel activé"
echo "✅ Dépendances vérifiées"
echo ""

# Lancer l'interface interactive
python launcher_interactif.py