// Composant Spider-Semantic pour analyser et afficher les émotions
class SpiderSemantic {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.canvas = null;
        this.ctx = null;
        this.data = null;          // Données normalisées pour l'affichage
        this.rawData = null;       // Données brutes originales  
        this.isAnimating = false;
        
        // Options par défaut
        this.options = {
            size: options.size || 300,
            categories: options.categories || [
                'Passion', 'Tendresse', 'Désir', 'Romance',
                'Mélancolie', 'Espoir', 'Sensualité', 'Poésie'
            ],
            colors: options.colors || {
                grid: 'rgba(255, 255, 255, 0.2)',
                fill: 'rgba(255, 107, 157, 0.3)',
                stroke: 'rgba(255, 107, 157, 0.8)',
                text: 'rgba(255, 255, 255, 0.9)',
                highlight: 'rgba(255, 230, 109, 1)'
            },
            animation: options.animation !== false
        };
        
        this.init();
    }
    
    init() {
        this.createCanvas();
        this.attachEvents();
        console.log('🕷️ Spider-Semantic initialisé');
    }
    
    createCanvas() {
        this.container.innerHTML = `
            <div class="spider-semantic">
                <h4>🕷️ Analyse Sémantique Émotionnelle</h4>
                <canvas id="spider-canvas" width="${this.options.size}" height="${this.options.size}"></canvas>
                <div class="spider-info" id="spider-info">
                    <p>En attente de données d'analyse...</p>
                </div>
            </div>
        `;
        
        this.canvas = this.container.querySelector('#spider-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.infoDiv = this.container.querySelector('#spider-info');
        
        // Configuration canvas haute résolution avec adaptation responsive
        const dpr = window.devicePixelRatio || 1;
        
        // Adapter la taille en fonction de l'écran
        let canvasSize;
        if (window.innerWidth <= 375) {
            canvasSize = 200;
        } else if (window.innerWidth <= 480) {
            canvasSize = 240;
        } else if (window.innerWidth <= 768) {
            canvasSize = 280;
        } else {
            canvasSize = this.options.size;
        }
        
        this.canvas.width = canvasSize * dpr;
        this.canvas.height = canvasSize * dpr;
        this.ctx.scale(dpr, dpr);
        
        this.canvas.style.width = canvasSize + 'px';
        this.canvas.style.height = canvasSize + 'px';
        
        // Mettre à jour le centre et le rayon pour la nouvelle taille
        this.center = { x: canvasSize / 2, y: canvasSize / 2 };
        this.radius = Math.min(canvasSize * 0.35, 120);
        
        // Dessiner la grille de base
        this.drawGrid();
    }
    
    attachEvents() {
        // Réactivité au redimensionnement
        window.addEventListener('resize', () => {
            clearTimeout(this.resizeTimeout);
            this.resizeTimeout = setTimeout(() => {
                this.createCanvas();
                if (this.data) {
                    this.updateData(this.data);
                }
            }, 250);
        });
        
        // Interaction tactile
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('touchstart', (e) => this.handleTouch(e), {passive: true});
    }
    
    drawGrid() {
        const centerX = this.options.size / 2;
        const centerY = this.options.size / 2;
        const maxRadius = Math.min(this.options.size, this.options.size) / 2.5;
        const categories = this.options.categories;
        
        this.ctx.clearRect(0, 0, this.options.size, this.options.size);
        
        // Cercles concentriques
        this.ctx.strokeStyle = this.options.colors.grid;
        this.ctx.lineWidth = 1;
        
        for (let r = maxRadius / 4; r <= maxRadius; r += maxRadius / 4) {
            this.ctx.beginPath();
            this.ctx.arc(centerX, centerY, r, 0, Math.PI * 2);
            this.ctx.stroke();
        }
        
        // Lignes radiales et labels
        this.ctx.fillStyle = this.options.colors.text;
        this.ctx.font = '11px Arial, sans-serif';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        const angleStep = (Math.PI * 2) / categories.length;
        
        for (let i = 0; i < categories.length; i++) {
            const angle = i * angleStep - Math.PI / 2;
            const x = Math.cos(angle) * maxRadius;
            const y = Math.sin(angle) * maxRadius;
            
            // Ligne radiale
            this.ctx.strokeStyle = this.options.colors.grid;
            this.ctx.beginPath();
            this.ctx.moveTo(centerX, centerY);
            this.ctx.lineTo(centerX + x, centerY + y);
            this.ctx.stroke();
            
            // Label de catégorie
            const labelX = centerX + Math.cos(angle) * (maxRadius + 25);
            const labelY = centerY + Math.sin(angle) * (maxRadius + 25);
            
            this.ctx.fillStyle = this.options.colors.text;
            this.ctx.fillText(categories[i], labelX, labelY);
        }
    }
    
    updateData(data, animated = true) {
        // Stocker les données brutes
        this.rawData = this.processData(data, true); // true = garder les valeurs brutes
        // Stocker les données normalisées pour l'affichage
        this.data = this.processData(data, false);   // false = normaliser
        
        if (animated && this.options.animation) {
            this.animateToData();
        } else {
            this.drawData();
        }
        
        this.updateInfo();
    }
    
    processData(data, keepRaw = false) {
        // Accepter plusieurs formats de données
        if (!data) return this.generateDefaultData();
        
        // Format direct: {category: value}
        if (typeof data === 'object' && !Array.isArray(data)) {
            return keepRaw ? this.getRawDataObject(data) : this.normalizeDataObject(data);
        }
        
        // Format métadonnées avec analyse
        if (data.love_analysis && data.love_analysis.emotions) {
            return keepRaw ? this.getRawDataObject(data.love_analysis.emotions) : this.normalizeDataObject(data.love_analysis.emotions);
        }
        
        // Format avec keywords - générer des valeurs basées sur les mots-clés
        if (data.keywords && Array.isArray(data.keywords)) {
            return this.generateDataFromKeywords(data.keywords);
        }
        
        return this.generateDefaultData();
    }
    
    getRawDataObject(obj) {
        const raw = {};
        const categories = this.options.categories;
        
        categories.forEach(category => {
            const key = this.findMatchingKey(obj, category);
            raw[category] = key ? obj[key] : Math.random() * 0.3;
        });
        
        return raw;
    }
    
    normalizeDataObject(obj) {
        const normalized = {};
        const categories = this.options.categories;
        const values = [];
        
        // D'abord, collecter toutes les valeurs pour calculer min/max
        categories.forEach(category => {
            const key = this.findMatchingKey(obj, category);
            if (key && obj[key] !== undefined) {
                values.push(obj[key]);
            }
        });
        
        // Calculer min/max pour une normalisation adaptative
        let minValue = Math.min(...values);
        let maxValue = Math.max(...values);
        
        // Si toutes les valeurs sont très proches, utiliser une échelle étendue
        const range = maxValue - minValue;
        if (range < 0.3) {
            // Étendre la plage pour de meilleures visualisations
            const center = (minValue + maxValue) / 2;
            const extendedRange = Math.max(0.4, range * 2);
            minValue = Math.max(0, center - extendedRange / 2);
            maxValue = Math.min(1, center + extendedRange / 2);
        }
        
        // Normaliser avec la nouvelle échelle (0.2 minimum pour visibilité)
        categories.forEach(category => {
            const key = this.findMatchingKey(obj, category);
            if (key && obj[key] !== undefined) {
                let normalizedValue;
                if (maxValue === minValue) {
                    normalizedValue = 0.5; // Valeur moyenne si toutes sont égales
                } else {
                    normalizedValue = (obj[key] - minValue) / (maxValue - minValue);
                }
                // Assurer une visibilité minimale (0.2) et maximale (0.95)
                normalized[category] = 0.2 + (normalizedValue * 0.75);
            } else {
                normalized[category] = Math.random() * 0.3 + 0.2;
            }
        });
        
        return normalized;
    }
    
    findMatchingKey(obj, category) {
        const keys = Object.keys(obj);
        const categoryLower = category.toLowerCase();
        
        // Recherche exacte
        let match = keys.find(key => key.toLowerCase() === categoryLower);
        if (match) return match;
        
        // Recherche partielle
        match = keys.find(key => key.toLowerCase().includes(categoryLower) || 
                               categoryLower.includes(key.toLowerCase()));
        return match;
    }
    
    generateDataFromKeywords(keywords) {
        const data = {};
        const categories = this.options.categories;
        
        categories.forEach(category => {
            let score = Math.random() * 0.2 + 0.1; // Score de base
            
            keywords.forEach(keyword => {
                if (this.isRelatedToCategory(keyword.toLowerCase(), category.toLowerCase())) {
                    score += Math.random() * 0.6 + 0.3;
                }
            });
            
            data[category] = Math.min(score, 1.0);
        });
        
        return data;
    }
    
    isRelatedToCategory(keyword, category) {
        const relations = {
            'passion': ['amour', 'passion', 'feu', 'ardent', 'brûler', 'intense'],
            'tendresse': ['tendresse', 'doux', 'caresse', 'câlin', 'gentillesse', 'bienveillance'],
            'désir': ['désir', 'envie', 'attraction', 'séduction', 'charme', 'vouloir'],
            'romance': ['romance', 'romantique', 'rêve', 'conte', 'prince', 'princesse'],
            'mélancolie': ['mélancolie', 'tristesse', 'nostalgie', 'absence', 'manque', 'peine'],
            'espoir': ['espoir', 'futur', 'demain', 'possible', 'ensemble', 'avenir'],
            'sensualité': ['sensuel', 'peau', 'toucher', 'corps', 'sensation', 'charnel'],
            'poésie': ['poésie', 'vers', 'rime', 'beauté', 'art', 'sublime']
        };
        
        return relations[category] && relations[category].includes(keyword);
    }
    
    generateDefaultData() {
        const data = {};
        this.options.categories.forEach(category => {
            data[category] = Math.random() * 0.7 + 0.3;
        });
        return data;
    }
    
    animateToData() {
        if (this.isAnimating) return;
        
        this.isAnimating = true;
        const startData = this.currentData || this.generateDefaultData();
        const endData = this.data;
        const duration = 1000; // 1 seconde
        const startTime = Date.now();
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = this.easeOutCubic(progress);
            
            const interpolatedData = {};
            this.options.categories.forEach(category => {
                const start = startData[category] || 0;
                const end = endData[category] || 0;
                interpolatedData[category] = start + (end - start) * eased;
            });
            
            this.drawData(interpolatedData);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                this.isAnimating = false;
                this.currentData = endData;
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }
    
    drawData(data = this.data) {
        if (!data) return;
        
        this.drawGrid();
        
        const centerX = this.options.size / 2;
        const centerY = this.options.size / 2;
        const maxRadius = Math.min(this.options.size, this.options.size) / 2.5;
        const categories = this.options.categories;
        const angleStep = (Math.PI * 2) / categories.length;
        
        // Dessiner le polygone de données
        this.ctx.fillStyle = this.options.colors.fill;
        this.ctx.strokeStyle = this.options.colors.stroke;
        this.ctx.lineWidth = 2;
        
        this.ctx.beginPath();
        
        categories.forEach((category, i) => {
            const angle = i * angleStep - Math.PI / 2;
            const value = data[category] || 0;
            const radius = value * maxRadius;
            
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;
            
            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }
        });
        
        this.ctx.closePath();
        this.ctx.fill();
        this.ctx.stroke();
        
        // Dessiner les points de données
        categories.forEach((category, i) => {
            const angle = i * angleStep - Math.PI / 2;
            const value = data[category] || 0;
            const radius = value * maxRadius;
            
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;
            
            this.ctx.fillStyle = this.options.colors.highlight;
            this.ctx.beginPath();
            this.ctx.arc(x, y, 4, 0, Math.PI * 2);
            this.ctx.fill();
        });
    }
    
    updateInfo() {
        if (!this.data) {
            this.infoDiv.innerHTML = '<p>En attente de données d\'analyse...</p>';
            return;
        }
        
        // Trouver les catégories dominantes
        const sortedCategories = this.options.categories
            .map(cat => ({ name: cat, value: this.data[cat] || 0 }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 3);
        
        const dominantEmotions = sortedCategories
            .map(cat => `${cat.name} (${(cat.value * 100).toFixed(0)}%)`)
            .join(', ');
        
        // Calculer le score global
        // Calculer l'intensité moyenne des données brutes
        const rawAvgScore = this.rawData ? 
            this.options.categories.reduce((sum, cat) => sum + (this.rawData[cat] || 0), 0) / this.options.categories.length : 
            0;
        
        // Créer une liste des émotions avec leurs valeurs brutes
        const emotionDetails = this.options.categories
            .map(cat => ({
                name: cat,
                raw: this.rawData ? (this.rawData[cat] || 0) : 0,
                normalized: this.data[cat] || 0
            }))
            .sort((a, b) => b.raw - a.raw)
            .slice(0, 3)
            .map(emotion => `${emotion.name} (${(emotion.raw * 100).toFixed(1)}%)`)
            .join(', ');
        
        this.infoDiv.innerHTML = `
            <div class="spider-stats">
                <p><strong>Émotions dominantes:</strong> ${emotionDetails}</p>
                <p><strong>Intensité moyenne:</strong> ${(rawAvgScore * 100).toFixed(1)}% <small>(brut)</small></p>
                <p><strong>Plage des valeurs:</strong> ${this.getValueRange()}</p>
                <p><small><em>🔍 Graphique normalisé pour une meilleure visibilité</em></small></p>
            </div>
        `;
    }
    
    getValueRange() {
        if (!this.rawData) return 'N/A';
        
        const values = this.options.categories.map(cat => this.rawData[cat] || 0);
        const min = Math.min(...values);
        const max = Math.max(...values);
        
        return `${(min * 100).toFixed(1)}% - ${(max * 100).toFixed(1)}%`;
    }
    
    handleClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // Détecter si on clique près d'un point de données
        const centerX = this.options.size / 2;
        const centerY = this.options.size / 2;
        const maxRadius = Math.min(this.options.size, this.options.size) / 2.5;
        const angleStep = (Math.PI * 2) / this.options.categories.length;
        
        this.options.categories.forEach((category, i) => {
            const angle = i * angleStep - Math.PI / 2;
            const value = this.data[category] || 0;
            const radius = value * maxRadius;
            
            const pointX = centerX + Math.cos(angle) * radius;
            const pointY = centerY + Math.sin(angle) * radius;
            
            const distance = Math.sqrt((x - pointX) ** 2 + (y - pointY) ** 2);
            
            if (distance < 15) {
                this.showTooltip(category, value, e);
            }
        });
    }
    
    handleTouch(e) {
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            this.handleClick({
                clientX: touch.clientX,
                clientY: touch.clientY
            });
        }
    }
    
    showTooltip(category, value, event) {
        // Simple alert pour le moment, peut être amélioré avec un vrai tooltip
        const percentage = (value * 100).toFixed(1);
        console.log(`🕷️ ${category}: ${percentage}%`);
        
        // Optionnel: créer un tooltip plus sophistiqué
        this.createTooltip(category, percentage, event);
    }
    
    createTooltip(category, percentage, event) {
        // Supprimer tooltip existant
        const existingTooltip = document.querySelector('.spider-tooltip');
        if (existingTooltip) {
            existingTooltip.remove();
        }
        
        // Créer nouveau tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'spider-tooltip';
        tooltip.innerHTML = `<strong>${category}</strong><br>${percentage}%`;
        
        tooltip.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            left: ${event.clientX + 10}px;
            top: ${event.clientY - 10}px;
        `;
        
        document.body.appendChild(tooltip);
        
        // Supprimer après 3 secondes
        setTimeout(() => {
            if (tooltip.parentNode) {
                tooltip.remove();
            }
        }, 3000);
    }
    
    // API publique
    clear() {
        this.data = null;
        this.drawGrid();
        this.updateInfo();
    }
    
    export() {
        return {
            data: this.data,
            categories: this.options.categories,
            timestamp: new Date().toISOString()
        };
    }
}

// Export pour utilisation globale
window.SpiderSemantic = SpiderSemantic;