#!/bin/bash

# Script de lancement du serveur spectacle d'amour
# Configuration pour serveur captif WiFi

echo "🎭 Démarrage du serveur spectacle d'amour..."

# Variables de configuration
PORT=3000
WEBSOCKET_PORT=8080
INTERFACE_DIR="/Users/yan/synoul415/devel/texts_AA/web-interface"
PYTHON_ENV="/Users/yan/synoul415/devel/texts_AA/.venv/bin/python"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "$INTERFACE_DIR" ]; then
    echo "❌ Répertoire interface non trouvé: $INTERFACE_DIR"
    exit 1
fi

cd "$INTERFACE_DIR"

# Vérifier Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js non installé. Installation requise:"
    echo "   brew install node"
    exit 1
fi

# Vérifier npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm non disponible"
    exit 1
fi

# Installer les dépendances si nécessaire
if [ ! -d "node_modules" ]; then
    echo "📦 Installation des dépendances Node.js..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Erreur lors de l'installation des dépendances"
        exit 1
    fi
fi

# Vérifier l'environnement Python
if [ ! -f "$PYTHON_ENV" ]; then
    echo "❌ Environnement Python non trouvé: $PYTHON_ENV"
    echo "   Exécutez d'abord: source .venv/bin/activate"
    exit 1
fi

# Vérifier que phrase_montage.py existe
PHRASE_SCRIPT="../examples/phrase_montage.py"
if [ ! -f "$PHRASE_SCRIPT" ]; then
    echo "❌ Script phrase_montage.py non trouvé: $PHRASE_SCRIPT"
    exit 1
fi

# Test du pont Python
echo "🐍 Test du pont Python..."
cd python-bridge
$PYTHON_ENV api_wrapper.py test > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  Attention: Test du pont Python échoué (continuons quand même)"
else
    echo "✅ Pont Python opérationnel"
fi
cd ..

# Arrêter les processus existants sur les ports
echo "🧹 Nettoyage des ports $PORT et $WEBSOCKET_PORT..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
lsof -ti:$WEBSOCKET_PORT | xargs kill -9 2>/dev/null || true

# Configuration réseau pour serveur captif
echo "🌐 Configuration réseau captive..."
echo "   Pour activer le portail captif WiFi:"
echo "   1. Configurer un hotspot WiFi"
echo "   2. Rediriger le trafic DNS vers ce serveur"
echo "   3. Configurer iptables pour redirection HTTP"

# Afficher l'IP locale
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "   IP locale détectée: $LOCAL_IP"

# Démarrer le serveur
echo "🚀 Démarrage du serveur..."
echo "   Interface web: http://localhost:$PORT"
echo "   Interface web (réseau): http://$LOCAL_IP:$PORT"
echo "   WebSocket: ws://localhost:$WEBSOCKET_PORT"
echo ""
echo "🎭 Serveur prêt pour le spectacle!"
echo "   Appuyez sur Ctrl+C pour arrêter"
echo ""

# Lancer le serveur Node.js
exec node server.js