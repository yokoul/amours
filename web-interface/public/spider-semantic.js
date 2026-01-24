// Composant Spider Semantic séparé - Analyse émotionnelle visuelle
class SpiderSemantic {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        this.options = {
            size: options.size || 300,
            categories: options.categories || [
                'Passion', 'Tendresse', 'Désir', 'Romance', 
                'Mélancolie', 'Espoir', 'Sensualité', 'Poésie'
            ],
            colors: options.colors || {
                background: 'rgba(40, 20, 60, 0.9)',
                grid: 'rgba(255, 255, 255, 0.1)',
                data: 'rgba(255, 100, 200, 0.6)',
                stroke: 'rgba(255, 150, 220, 1)',
                labels: 'rgba(255, 255, 255, 0.8)',
                points: 'rgba(255, 200, 255, 1)'
            }
        };
        
        this.data = {};
        this.animatedData = {};
        this.isAnimating = false;
        
        this.init();
    }
    
    init() {
        this.setupCanvas();
        this.generateDefaultData();
        this.render();
        
        console.log('🕷️ SpiderSemantic initialisé');
    }
    
    setupCanvas() {
        const size = this.options.size;
        this.canvas.width = size;
        this.canvas.height = size;
        this.canvas.style.width = `${size}px`;
        this.canvas.style.height = `${size}px`;
        
        this.center = {
            x: size / 2,
            y: size / 2
        };
        this.radius = size * 0.35; // Rayon maximum du spider
    }
    
    generateDefaultData() {
        // Données par défaut aléatoires
        this.options.categories.forEach(category => {
            this.data[category] = Math.random() * 0.6 + 0.2; // Entre 0.2 et 0.8
            this.animatedData[category] = this.data[category];
        });
    }
    
    setData(newData, animate = true) {
        // Mettre à jour les données avec validation
        Object.keys(newData).forEach(category => {
            if (this.options.categories.includes(category)) {
                this.data[category] = Math.max(0, Math.min(1, newData[category]));
            }
        });
        
        if (animate) {
            this.animateToNewData();
        } else {
            this.animatedData = { ...this.data };
            this.render();
        }
    }
    
    animateToNewData() {
        if (this.isAnimating) return;
        
        this.isAnimating = true;
        const startData = { ...this.animatedData };
        const startTime = Date.now();
        const duration = 800; // 800ms d'animation
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Interpolation fluide (easing)
            const easeProgress = this.easeInOutCubic(progress);
            
            // Interpoler chaque catégorie
            this.options.categories.forEach(category => {
                const start = startData[category] || 0;
                const end = this.data[category] || 0;
                this.animatedData[category] = start + (end - start) * easeProgress;
            });
            
            this.render();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                this.isAnimating = false;
            }
        };
        
        animate();
    }
    
    easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
    }
    
    render() {
        const ctx = this.ctx;
        const center = this.center;
        const radius = this.radius;
        
        // Clear
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Background
        ctx.fillStyle = this.options.colors.background;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Grille concentrique
        this.drawGrid(ctx, center, radius);
        
        // Axes radiaux
        this.drawRadialAxes(ctx, center, radius);
        
        // Données spider
        this.drawSpiderData(ctx, center, radius);
        
        // Labels
        this.drawLabels(ctx, center, radius);
        
        // Titre
        this.drawTitle(ctx);
    }
    
    drawGrid(ctx, center, radius) {
        ctx.strokeStyle = this.options.colors.grid;
        ctx.lineWidth = 1;
        
        // Cercles concentriques
        for (let i = 1; i <= 4; i++) {
            const r = (radius * i) / 4;
            ctx.beginPath();
            ctx.arc(center.x, center.y, r, 0, Math.PI * 2);
            ctx.stroke();
        }
    }
    
    drawRadialAxes(ctx, center, radius) {
        const categories = this.options.categories;
        const angleStep = (Math.PI * 2) / categories.length;
        
        ctx.strokeStyle = this.options.colors.grid;
        ctx.lineWidth = 1;
        
        for (let i = 0; i < categories.length; i++) {
            const angle = i * angleStep - Math.PI / 2; // Commencer en haut
            const x = center.x + Math.cos(angle) * radius;
            const y = center.y + Math.sin(angle) * radius;
            
            ctx.beginPath();
            ctx.moveTo(center.x, center.y);
            ctx.lineTo(x, y);
            ctx.stroke();
        }
    }
    
    drawSpiderData(ctx, center, radius) {
        const categories = this.options.categories;
        const angleStep = (Math.PI * 2) / categories.length;
        
        // Zone remplie
        ctx.fillStyle = this.options.colors.data;
        ctx.strokeStyle = this.options.colors.stroke;
        ctx.lineWidth = 2;
        
        ctx.beginPath();
        
        for (let i = 0; i < categories.length; i++) {
            const angle = i * angleStep - Math.PI / 2;
            const value = this.animatedData[categories[i]] || 0;
            const distance = radius * value;
            
            const x = center.x + Math.cos(angle) * distance;
            const y = center.y + Math.sin(angle) * distance;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
        
        // Points de données
        ctx.fillStyle = this.options.colors.points;
        
        for (let i = 0; i < categories.length; i++) {
            const angle = i * angleStep - Math.PI / 2;
            const value = this.animatedData[categories[i]] || 0;
            const distance = radius * value;
            
            const x = center.x + Math.cos(angle) * distance;
            const y = center.y + Math.sin(angle) * distance;
            
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    drawLabels(ctx, center, radius) {
        const categories = this.options.categories;
        const angleStep = (Math.PI * 2) / categories.length;
        
        ctx.fillStyle = this.options.colors.labels;
        ctx.font = '12px Arial, sans-serif';
        ctx.textAlign = 'center';
        
        for (let i = 0; i < categories.length; i++) {
            const angle = i * angleStep - Math.PI / 2;
            const labelDistance = radius + 25;
            
            const x = center.x + Math.cos(angle) * labelDistance;
            const y = center.y + Math.sin(angle) * labelDistance;
            
            // Ajuster l'alignement selon la position
            if (Math.cos(angle) < -0.1) {
                ctx.textAlign = 'right';
            } else if (Math.cos(angle) > 0.1) {
                ctx.textAlign = 'left';
            } else {
                ctx.textAlign = 'center';
            }
            
            ctx.fillText(categories[i], x, y + 4);
            
            // Afficher la valeur
            const value = this.animatedData[categories[i]] || 0;
            ctx.font = '10px Arial, sans-serif';
            ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
            ctx.fillText(`${(value * 100).toFixed(0)}%`, x, y + 18);
            
            // Restaurer pour le prochain label
            ctx.font = '12px Arial, sans-serif';
            ctx.fillStyle = this.options.colors.labels;
        }
    }
    
    drawTitle(ctx) {
        ctx.fillStyle = this.options.colors.labels;
        ctx.font = 'bold 14px Arial, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Analyse Sémantique', this.center.x, 25);
        
        ctx.font = '11px Arial, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        ctx.fillText('Intensité émotionnelle', this.center.x, 42);
    }
    
    // Méthodes d'analyse des mots-clés
    analyzeKeywords(keywords) {
        const analysis = {};
        
        // Réinitialiser
        this.options.categories.forEach(cat => analysis[cat] = 0.1);
        
        // Dictionnaire d'associations émotionnelles
        const emotionalMap = {
            'passion': ['passion', 'ardent', 'brûle', 'feu', 'intense', 'amour', 'fort'],
            'tendresse': ['tendresse', 'doux', 'caresse', 'câlin', 'tendre', 'bienveillant'],
            'désir': ['désir', 'envie', 'attraction', 'séduction', 'charme', 'attirance'],
            'romance': ['romance', 'romantique', 'rêve', 'conte', 'prince', 'princesse'],
            'mélancolie': ['mélancolie', 'tristesse', 'nostalgie', 'absence', 'manque', 'loin'],
            'espoir': ['espoir', 'futur', 'demain', 'possible', 'ensemble', 'avenir'],
            'sensualité': ['sensuel', 'peau', 'toucher', 'corps', 'sensation', 'plaisir'],
            'poésie': ['poésie', 'vers', 'rime', 'beauté', 'art', 'sublime']
        };
        
        // Analyser chaque mot-clé
        keywords.forEach(keyword => {
            const word = keyword.toLowerCase();
            
            Object.keys(emotionalMap).forEach(emotion => {
                if (emotionalMap[emotion].some(term => word.includes(term) || term.includes(word))) {
                    const categoryKey = emotion.charAt(0).toUpperCase() + emotion.slice(1);
                    if (analysis[categoryKey] !== undefined) {
                        analysis[categoryKey] += 0.3 + Math.random() * 0.4; // 0.3 à 0.7 d'augmentation
                    }
                }
            });
        });
        
        // Normaliser les valeurs entre 0 et 1
        Object.keys(analysis).forEach(key => {
            analysis[key] = Math.min(1, analysis[key]);
        });
        
        return analysis;
    }
    
    updateFromTrack(track) {
        if (!track || !track.keywords) return;
        
        const analysis = this.analyzeKeywords(track.keywords);
        this.setData(analysis, true);
        
        console.log('🕷️ Spider mis à jour:', analysis);
    }
    
    // API publique
    resize(newSize) {
        this.options.size = newSize;
        this.setupCanvas();
        this.render();
    }
    
    setColors(newColors) {
        Object.assign(this.options.colors, newColors);
        this.render();
    }
    
    getData() {
        return { ...this.data };
    }
}

// Export
window.SpiderSemantic = SpiderSemantic;