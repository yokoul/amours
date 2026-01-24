# 🕷️ Test du Spider Sémantique

## Étapes pour tester

1. **Ouvrir la console du navigateur** (F12 ou Cmd+Option+I)
   
2. **Recharger complètement** (Cmd+Shift+R sur Mac, Ctrl+Shift+R sur PC)

3. **Créer une phrase** :
   - Cliquer sur "toucher pour commencer"
   - Sélectionner 2-3 mots (ex: amour, passion, tendresse)
   - Cliquer sur "créer"

4. **Observer dans la console** :
   ```
   📦 Résultat reçu: {...}
   🕷️ showSemanticVisualization appelé avec: {...}
   🕷️ Spider affiché
   ```

5. **Vérifier visuellement** :
   - Le spider devrait apparaître sous le lecteur audio
   - Forme octogonale en noir et blanc
   - Labels des types d'amour autour
   - Animation douce d'apparition

## Debug si ça ne marche pas

### Cas 1: Aucun log "🕷️"
→ Le spider n'est pas appelé, vérifier que `semantic_analysis` est dans la réponse

### Cas 2: Log "⚠️ Pas de données sémantiques"
→ Les données ne sont pas chargées depuis les fichiers JSON

### Cas 3: Erreur "SpiderMinimal is not defined"
→ Le fichier spider-minimal.js n'est pas chargé

### Cas 4: Spider invisible mais logs OK
→ Problème CSS, vérifier avec l'inspecteur d'éléments

## Commandes utiles

```bash
# Vérifier les logs du serveur
cd /Users/yan/synoul415/devel/texts_AA/web-interface
pkill -f "node poetic-server.js" && node poetic-server.js

# Tester la génération Python directement
cd /Users/yan/synoul415/devel/texts_AA
.venv/bin/python web-interface/web_phrase_generator.py 2 amour passion 2>&1 | grep semantic
```
