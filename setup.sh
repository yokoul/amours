#!/bin/bash
# Script d'installation et configuration du projet Amours

set -e

echo "🎵 Configuration du projet Amours - Analyse des Types d'Amour ❤️"
echo "================================================================"

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION détecté"

# Créer l'environnement virtuel si nécessaire
if [ ! -d ".venv" ]; then
    echo "🔧 Création de l'environnement virtuel..."
    python3 -m venv .venv
fi

# Activer l'environnement virtuel
echo "🔌 Activation de l'environnement virtuel..."
source .venv/bin/activate

# Mettre à jour pip
echo "⬆️ Mise à jour de pip..."
python -m pip install --upgrade pip

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Créer les dossiers nécessaires
echo "📁 Création des dossiers de travail..."
mkdir -p audio
mkdir -p output_transcription
mkdir -p output_semantic
mkdir -p output_sentences

# Vérifier l'installation
echo "🧪 Vérification de l'installation..."
python -c "
import whisper
import sentence_transformers
print('✅ Whisper AI installé')
print('✅ Sentence Transformers installé')
"

echo ""
echo "🎉 Installation terminée avec succès !"
echo ""
echo "📋 Prochaines étapes :"
echo "  1. Placez vos fichiers audio dans le dossier 'audio/'"
echo "  2. Lancez l'interface : ./launch.sh"
echo "  3. Ou utilisez : python launcher_interactif.py"
echo ""
echo "📖 Consultez le README.md pour plus d'informations"
echo ""
echo "❤️ Bon analyse des sentiments amoureux !"