#!/bin/bash
# Script de génération/régénération des certificats SSL pour HTTPS

cd "$(dirname "$0")"
mkdir -p ssl

# Récupérer l'IP locale
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo "🔐 Génération des certificats SSL..."
echo "📍 IP locale détectée: $LOCAL_IP"

# Créer le fichier de configuration OpenSSL
cat > ssl/openssl.cnf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_req

[dn]
CN = localhost

[v3_req]
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = today.local
DNS.3 = *.local
IP.1 = 127.0.0.1
IP.2 = $LOCAL_IP
EOF

# Générer le certificat
cd ssl
openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 365 \
    -keyout key.pem \
    -out cert.pem \
    -config openssl.cnf

echo ""
echo "✅ Certificats SSL générés !"
echo ""
echo "Certificat valide pour :"
openssl x509 -in cert.pem -text -noout | grep -A 1 "Subject Alternative Name"
echo ""
echo "🎭 Vous pouvez maintenant démarrer le serveur avec: node poetic-server.js"
