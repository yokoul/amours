# Interface Web Spectacle d'Amour 🎭

Interface web captive pour spectacle interactif de génération de phrases d'amour, utilisant les technologies de transcription audio existantes.

## ✨ Fonctionnalités

- **Interface tactile optimisée mobile** avec damier de mots interactifs
- **Visualisations artistiques P5.js** synchronisées avec les interactions
- **Serveur captif WiFi** pour redirection automatique du public
- **Intégration transparente** avec `phrase_montage.py` existant
- **WebSockets temps réel** pour synchronisation multi-utilisateurs
- **Animations et effets** pour expérience immersive

## 🚀 Démarrage rapide

```bash
# Aller dans le répertoire interface
cd web-interface

# Installer les dépendances Node.js
npm install

# Lancer le serveur
./start-server.sh
```

L'interface sera accessible sur:
- Local: http://localhost:3000
- Réseau: http://[IP-locale]:3000

## 📱 Utilisation

1. **Connexion**: Les utilisateurs se connectent au WiFi du spectacle
2. **Redirection**: Ils sont automatiquement redirigés vers l'interface
3. **Sélection**: Damier de 20 mots (incluant toujours "amour")
4. **Génération**: Nombre de mots sélectionnés = nombre de phrases générées
5. **Résultat**: Affichage des phrases avec éventuellement lecture audio

## 🏗️ Architecture

```
web-interface/
├── server.js              # Serveur Express + WebSocket
├── package.json           # Dépendances Node.js
├── start-server.sh        # Script de lancement
├── public/
│   ├── index.html         # Interface principale
│   ├── style.css          # Styles responsive mobile
│   ├── app.js             # Logique client JavaScript
│   └── p5-background.js   # Animations P5.js
├── python-bridge/
│   └── api_wrapper.py     # Pont vers phrase_montage.py
└── CAPTIVE-SETUP.md       # Configuration serveur captif
```

## 🔄 Intégration existante

Le serveur utilise directement votre script `phrase_montage.py`:

```javascript
// Dans server.js
const pythonProcess = spawn('python', [
    'examples/phrase_montage.py',
    word_count.toString(),
    ...selected_words
]);
```

## 🎨 Interface utilisateur

### Damier de mots
- 4x5 grille responsive
- "Amour" toujours présent (mis en valeur)
- 19 mots aléatoires du vocabulaire d'amour
- Animation d'apparition séquentielle
- Feedback tactile et visuel

### Visualisations P5.js
- Particules d'amour flottantes
- Ondes d'émotion expansives
- Battements de cœur synchronisés
- Réactions aux interactions utilisateur
- Intensité variable selon l'activité

### Contrôles
- Sélection multiple de mots
- Génération basée sur le nombre sélectionné
- Actualisation du vocabulaire
- Nouvelle création

## 🌐 Serveur captif

Pour configuration complète WiFi captive, voir [CAPTIVE-SETUP.md](CAPTIVE-SETUP.md).

Configuration simplifiée:
1. Créer hotspot WiFi "Spectacle-Amour"
2. Configurer DNS pour rediriger vers le serveur
3. Lancer l'interface web

## 🛠️ Développement

### Variables importantes
```javascript
const PORT = 3000;           // Port interface web
const WEBSOCKET_PORT = 8080; // Port WebSocket
```

### API Endpoints
- `GET /` - Interface principale
- `GET /api/random-words/:count` - Mots aléatoires
- `POST /api/generate-phrase` - Génération de phrases
- `WS ws://localhost:8080` - WebSocket temps réel

### Structure des données
```json
{
  "words": ["amour", "passion", "désir"],
  "count": 3,
  "result": "Phrase générée par phrase_montage.py"
}
```

## 🎭 Personnalisation spectacle

### Vocabulaire
Modifier `love_vocabulary` dans `server.js` pour personnaliser les mots disponibles.

### Animations
Ajuster les paramètres P5.js dans `p5-background.js`:
- `currentIntensity` - Intensité des animations
- Nombre de particules, ondes, battements
- Couleurs et effets visuels

### Interface
Personnaliser `style.css` pour:
- Couleurs du thème (variables CSS)
- Taille des éléments tactiles
- Animations et transitions

## 📦 Dépendances

### Node.js
- `express` - Serveur web
- `ws` - WebSockets
- `cors` - CORS policy
- `multer` - Upload de fichiers (future extension)

### Python
- Environnement virtuel existant
- Modules requis par `phrase_montage.py`

## 🔧 Maintenance

### Logs
```bash
# Serveur Node.js
# Affichés dans le terminal

# Test pont Python
cd python-bridge
python api_wrapper.py test
```

### Monitoring
- Connexions WebSocket actives
- Statut des générations Python
- Utilisation mémoire/CPU

## 🎪 Utilisation en spectacle

1. **Pré-spectacle**: Configurer WiFi et tester l'interface
2. **Pendant**: Les spectateurs interagissent via leurs mobiles
3. **Post-spectacle**: Nettoyer la configuration réseau

### Conseils spectacle
- Prévoir une connexion de secours
- Tester avec plusieurs appareils simultanément
- Monitorer les performances du serveur
- Prévoir un mode dégradé sans WiFi captif

---

🎭 **Prêt pour le spectacle !** L'interface transforme votre technologie de transcription en expérience interactive pour le public.