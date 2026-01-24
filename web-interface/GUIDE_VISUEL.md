# Guide Visuel - Interface Poétique Minimaliste

## Flux d'Interaction

```
┌─────────────────────────────────────────────────┐
│                                                 │
│              ÉTAT 1: CONTEMPLATION              │
│                                                 │
│                     ╭─────╮                     │
│                    │  ○  │  <-- Cercle pulsant │
│                     ╰─────╯                     │
│                                                 │
│            "toucher pour commencer"             │
│                                                 │
└─────────────────────────────────────────────────┘
                        │
                        │ [TAP / ENTER]
                        ▼
┌─────────────────────────────────────────────────┐
│                                                 │
│              ÉTAT 2: INSPIRATION                │
│                                                 │
│   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │
│   │ âme │ │souffle││émoi│ │regard│ │silence│   │
│   └─────┘ └─────┘ └─────┘ └─────┘ └─────┘    │
│   ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐    │
│   │passion││lumière││vertige││caresse││murmure│ │
│   └─────┘ └─────┘ └─────┘ └─────┘ └─────┘    │
│                                                 │
│              Sélection: [âme] [regard]          │
│                                                 │
│                  ┌─────────┐                    │
│                  │  créer  │                    │
│                  └─────────┘                    │
│                                                 │
└─────────────────────────────────────────────────┘
                        │
                        │ [GÉNÉRER]
                        ▼
┌─────────────────────────────────────────────────┐
│                                                 │
│               ÉTAT 3: CRÉATION                  │
│                                                 │
│     ┌───────────────────────────────────┐      │
│     │  ▃ ▅ ▇ █ ▇ ▅ ▃ ▅ ▇ ▅ ▃  <-- Waveform│   │
│     └───────────────────────────────────┘      │
│                                                 │
│         ╭─────╮                                │
│        │  ▶  │  ━━━━━━━━━━━━━━━○            │
│         ╰─────╯        Progression             │
│                                                 │
│    "ton âme dans mon regard éternel"           │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Navigation & Contrôles

### Boutons Persistants (en bas)

```
    ╭───╮     ╭───╮
   │ ↺ │    │ ≡ │
    ╰───╯     ╰───╯
  Restart   Archive
```

### Archive (slide up)

```
┌─────────────────────────────────────────────────┐
│  mémoire                                    ×   │
├─────────────────────────────────────────────────┤
│                                                 │
│  23 jan, 19:45 • âme + regard                  │
│  ton âme dans mon regard éternel                │
│  ─────────────────────────────────────────────  │
│                                                 │
│  23 jan, 19:32 • passion + silence             │
│  la passion silencieuse de nos cœurs           │
│  ─────────────────────────────────────────────  │
│                                                 │
│  [Plus d'entrées...]                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Interactions Tactiles

### Mobile
- **Tap court** : Sélection immédiate (mots, boutons)
- **Tap long (500ms)** : Sélection intentionnelle sur mots
- **Swipe up** : Ouvrir l'archive
- **Swipe down** : Fermer l'archive (si ouverte)

### Desktop
- **Clic** : Sélection et actions
- **Hover** : Feedback visuel (gris → noir)
- **Tab** : Navigation au clavier
- **Enter/Space** : Activation

## États Visuels

### Boutons

#### Normal
```
┌─────────┐
│  créer  │  (border: noir, bg: blanc, opacity: 0.5)
└─────────┘
```

#### Hover
```
┌─────────┐
│  créer  │  (border: noir, bg: gris clair, opacity: 1)
└─────────┘
```

#### Active
```
┌─────────┐
│  créer  │  (border: noir, bg: noir, color: blanc)
└─────────┘
```

#### Disabled
```
┌─────────┐
│  créer  │  (border: gris, opacity: 0.5, non cliquable)
└─────────┘
```

### Mots

#### Non sélectionné
```
┌─────┐
│ âme │  (border: gris, bg: transparent)
└─────┘
```

#### Sélectionné
```
┌─────┐
│ âme │  (border: noir, bg: noir, color: blanc)
└─────┘
```

## Animations

### Durées
- **Rapide** : 0.3s (hover, tap feedback)
- **Moyen** : 0.8s (transitions boutons)
- **Lent** : 1.2s (transitions d'état)

### Types
- **Fade** : Opacity 0 → 1
- **Slide** : TranslateY(-20px → 0)
- **Scale** : Transform scale(0.95 → 1)
- **Pulse** : Animation continue du cercle d'entrée

## Responsive

### Mobile (< 480px)
- Espacements réduits
- Cercle : 100px
- Bouton play : 60px
- Font : 14px mots

### Tablet/Desktop (> 480px)
- Espacements standards
- Cercle : 120px
- Bouton play : 80px
- Font : 16px mots
- Max-width conteneurs : 400-500px

## Accessibilité

### ARIA
- `aria-label` : Tous les boutons
- `aria-live="polite"` : Zones dynamiques
- `role="button"` : Éléments cliquables non-button
- `role="progressbar"` : Barre de progression

### Focus
- Outline noir 2px
- Offset 4px
- Visible sur tous les éléments interactifs

### Clavier
- Tab : Navigation séquentielle
- Enter/Space : Activation
- Shift+Tab : Navigation inverse
- Escape : Fermeture modales (à implémenter)

## Performance

### Optimisations CSS
- `transform` et `opacity` uniquement (GPU)
- `will-change` sur éléments animés
- `-webkit-tap-highlight-color: transparent`
- `touch-action: manipulation`

### Optimisations JS
- Debounce sur resize
- RequestAnimationFrame pour canvas
- LocalStorage avec try/catch
- Gestion mémoire audio (remove)

## Palette Complète

```css
Background : #FFFFFF (blanc pur)
Texte      : #000000 (noir pur)
Bordures   : #999999 (gris moyen)
Hover      : #F5F5F5 (gris très clair)
Disabled   : #333333 (gris foncé)
```

## Typographie

```
Font Family : SF Pro Display, Helvetica Neue, Arial
Poids       : 300 (light) - 400 (regular)
Taille Base : 16px
Lettrage    : 1-2px (espacement élégant)
Hauteur     : 1.6-1.8 (lisibilité optimale)
Casse       : lowercase (esthétique minimaliste)
```
