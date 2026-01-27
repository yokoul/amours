#!/bin/bash
# Script de démarrage du serveur poétique avec HTTPS

cd "$(dirname "$0")"

echo "🔐 Démarrage du serveur poétique avec HTTPS..."
echo ""

# Vérifier que les certificats existent
if [ ! -f "ssl/key.pem" ] || [ ! -f "ssl/cert.pem" ]; then
    echo "❌ Certificats SSL introuvables !"
    echo "💡 Génération des certificats..."
    
    mkdir -p ssl
    openssl req -x509 -newkey rsa:2048 -nodes -sha256 \
        -subj '/CN=localhost' \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -days 365
    
    echo ""
    echo "✅ Certificats SSL générés dans ssl/"
    echo ""
fi

node poetic-server.js
