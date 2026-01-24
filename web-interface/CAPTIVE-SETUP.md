# Configuration Serveur Captif WiFi pour Spectacle d'Amour

## Installation des dépendances système

### macOS (avec Homebrew)
```bash
# Installer Node.js si pas déjà fait
brew install node

# Installer dnsmasq pour serveur DNS
brew install dnsmasq

# Installer hostapd pour hotspot (optionnel)
# brew install hostapd
```

### Configuration DNS captive

#### 1. Configuration dnsmasq
```bash
# Créer le fichier de config
sudo tee /usr/local/etc/dnsmasq.conf > /dev/null <<EOF
# Interface réseau (remplacer par votre interface WiFi)
interface=en0

# Plage DHCP pour les clients
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,12h

# Rediriger toutes les requêtes DNS vers notre serveur
address=/#/192.168.4.1

# Serveur DNS upstream (si besoin accès internet)
server=8.8.8.8
server=8.8.4.4

# Log pour debug
log-queries
log-dhcp
EOF
```

#### 2. Configuration réseau
```bash
# Configurer l'interface réseau (exemple)
sudo ifconfig en0 192.168.4.1 netmask 255.255.255.0

# Démarrer dnsmasq
sudo brew services start dnsmasq
```

#### 3. Redirection HTTP (iptables/pfctl sur macOS)
```bash
# Sur macOS, utiliser pfctl
sudo tee /etc/pf.anchors/captive > /dev/null <<EOF
# Redirection HTTP vers notre serveur
rdr on en0 inet proto tcp from any to any port 80 -> 127.0.0.1 port 3000
rdr on en0 inet proto tcp from any to any port 443 -> 127.0.0.1 port 3000
EOF

# Activer la règle
echo "rdr-anchor \"captive\"" | sudo pfctl -f -
sudo pfctl -a captive -f /etc/pf.anchors/captive
sudo pfctl -e
```

## Configuration serveur Node.js pour captif

### Variables d'environnement
```bash
export CAPTIVE_MODE=true
export CAPTIVE_IP=192.168.4.1
export CAPTIVE_PORT=3000
```

### Modifications server.js pour captif
Le serveur est déjà configuré pour gérer:
- Redirection automatique vers l'interface
- Route catch-all pour serveur captif
- Headers spéciaux pour détection portail captif

## Démarrage complet

### Script automatisé
```bash
# Lancer le serveur avec toute la configuration
./start-server.sh
```

### Vérification
1. **Test DNS**: `nslookup google.com 192.168.4.1`
2. **Test HTTP**: `curl http://any-domain.com` → doit rediriger vers l'interface
3. **Test mobile**: Se connecter au WiFi et ouvrir un navigateur

## Configuration WiFi Hotspot

### Méthode 1: Partage macOS
1. Préférences Système → Partage
2. Cocher "Partage Internet"
3. Partager depuis: Ethernet/WiFi
4. Vers: WiFi
5. Options WiFi: Nom "Spectacle-Amour", Mot de passe

### Méthode 2: create_ap (Linux/macOS)
```bash
# Installer create_ap
git clone https://github.com/oblique/create_ap
cd create_ap
sudo make install

# Lancer le hotspot
sudo create_ap en0 en1 Spectacle-Amour motdepasse --no-internet
```

## Troubleshooting

### Logs utiles
```bash
# Logs dnsmasq
tail -f /usr/local/var/log/dnsmasq.log

# Logs serveur Node
# Affichés directement dans le terminal

# Test connectivité
ping 192.168.4.1
telnet 192.168.4.1 3000
```

### Problèmes courants
- **Clients ne se connectent pas**: Vérifier DHCP et DNS
- **Pas de redirection**: Vérifier pfctl/iptables
- **Interface ne s'affiche pas**: Vérifier port 3000 et routes
- **Script Python échoue**: Vérifier environnement virtuel Python

### Nettoyage
```bash
# Arrêter services
sudo brew services stop dnsmasq
sudo pfctl -d
sudo pfctl -F all

# Reset interface
sudo ifconfig en0 down
sudo ifconfig en0 up
```

## Sécurité

⚠️ **Attention**: Cette configuration ouvre un serveur web local et modifie la configuration réseau. À utiliser uniquement dans un environnement contrôlé pour le spectacle.

### Bonnes pratiques:
- Utiliser uniquement pendant le spectacle
- Désactiver après usage
- Isoler le réseau du réseau principal
- Surveiller les connexions