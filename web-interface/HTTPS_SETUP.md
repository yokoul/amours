# Configuration HTTPS pour le Serveur Poétique

## Pourquoi HTTPS ?

L'accès au microphone est **obligatoire en HTTPS** sur iOS/Safari, même en développement local. Le serveur poétique détecte automatiquement la présence de certificats SSL et active HTTPS si disponible.

## Génération des certificats SSL

### Première installation

Les certificats sont générés automatiquement au premier démarrage avec le script `start-https.sh`, mais vous pouvez aussi les générer manuellement :

```bash
cd web-interface
mkdir -p ssl
cd ssl

# Créer le fichier de configuration OpenSSL
cat > openssl.cnf << EOF
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
IP.2 = VOTRE_IP_LOCALE
EOF

# Remplacer VOTRE_IP_LOCALE par votre IP (trouvée avec ifconfig)

# Générer le certificat
openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 365 \
    -keyout key.pem \
    -out cert.pem \
    -config openssl.cnf
```

### Régénération des certificats

Si votre IP locale change ou si vous voulez ajouter d'autres domaines :

```bash
cd web-interface/ssl

# 1. Modifier openssl.cnf pour ajouter vos domaines/IPs
nano openssl.cnf

# 2. Régénérer les certificats
rm -f cert.pem key.pem
openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 365 \
    -keyout key.pem \
    -out cert.pem \
    -config openssl.cnf

# 3. Vérifier les Subject Alternative Names
openssl x509 -in cert.pem -text -noout | grep -A 1 "Subject Alternative Name"

# 4. Redémarrer le serveur
```

### Trouver votre IP locale

```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}'

# Ou plus simple sur macOS
ifconfig en0 | grep "inet " | awk '{print $2}'
```

## Démarrage du serveur

### Avec HTTPS (recommandé pour iOS)

```bash
cd web-interface
node poetic-server.js
```

Le serveur détecte automatiquement les certificats SSL et démarre en HTTPS.

### Script de démarrage

Vous pouvez aussi utiliser le script qui génère les certificats si nécessaire :

```bash
cd web-interface
./start-https.sh
```

## Accès depuis différents appareils

Une fois le serveur démarré, vous verrez les URLs disponibles :

```
🎭 Interface poétique démarrée (HTTPS):
   → https://localhost:3000
   → https://10.10.100.193:3000 (réseau local)
   → https://today.local:3000 (mDNS)
```

### Sur Mac (local)

- `https://localhost:3000`

### Sur iPhone/iPad (même réseau WiFi)

- `https://today.local:3000` (si mDNS fonctionne)
- `https://10.10.100.193:3000` (avec l'IP affichée)

### Première connexion sur iOS

1. Ouvrir Safari et accéder à l'URL HTTPS
2. Safari affichera un avertissement de certificat
3. Cliquer sur **"Afficher les détails"**
4. Cliquer sur **"Visiter ce site web"**
5. Le certificat sera accepté pour toute la session

## Certificats inclus par défaut

Le certificat généré inclut :

- `DNS.1 = localhost` - Pour accès local sur Mac
- `DNS.2 = today.local` - Pour accès via mDNS (Bonjour)
- `DNS.3 = *.local` - Wildcard pour tous les domaines .local
- `IP.1 = 127.0.0.1` - Loopback
- `IP.2 = 10.10.100.193` - IP locale du Mac (à adapter)

## Dépannage

### Le microphone ne fonctionne pas sur iOS

- ✅ Vérifiez que vous êtes en **HTTPS** (URL commence par `https://`)
- ✅ Vérifiez que vous avez **accepté le certificat** (pas de "Non sécurisé" dans Safari)
- ✅ Vérifiez les **permissions** : Réglages → Safari → Microphone → Autoriser

### Le certificat n'est pas reconnu

```bash
# Vérifier que les fichiers existent
ls -la web-interface/ssl/

# Devrait afficher :
# cert.pem
# key.pem
# openssl.cnf

# Vérifier le contenu du certificat
openssl x509 -in web-interface/ssl/cert.pem -text -noout
```

### Le serveur démarre en HTTP au lieu de HTTPS

Le serveur utilise automatiquement HTTPS si les certificats sont présents. Si vous voyez :

```
⚠️  Mode HTTP: le microphone ne fonctionnera pas sur iOS
```

C'est que les certificats n'ont pas été trouvés. Générez-les avec :

```bash
cd web-interface
./start-https.sh
```

## Sécurité

⚠️ **Important** : Ces certificats sont **auto-signés** et destinés uniquement au **développement local**. 

- Ne PAS les utiliser en production
- Ne PAS les committer dans Git (déjà dans `.gitignore`)
- Régénérer régulièrement (validité : 365 jours)

## Mode HTTP (fallback)

Si vous n'avez pas besoin du microphone sur iOS, vous pouvez supprimer les certificats pour revenir en HTTP :

```bash
rm -rf web-interface/ssl/*.pem
```

Le serveur démarrera automatiquement en HTTP.
