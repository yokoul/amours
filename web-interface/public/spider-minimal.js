/* ===========================
   SPIDER MINIMAL - VISUALISATION SÉMANTIQUE
   Style minimaliste noir/blanc pour interface poétique
   =========================== */

class SpiderMinimal {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.canvas = null;
        this.ctx = null;
        this.data = null;
        this.animatedData = {};
        this.isAnimating = false;
        
        // Options minimalistes
        this.options = {
            size: options.size || 280,
            categories: options.categories || [
                'romantique', 'passionnel', 'tendre', 'physique',
                'platonique', 'familial', 'amical', 'spirituel'
            ],
            colors: {
                background: 'transparent',
                grid: 'rgba(0, 0, 0, 0.1)',
                data: 'rgba(0, 0, 0, 0.15)',
                stroke: 'rgba(0, 0, 0, 0.8)',
                text: 'rgba(0, 0, 0, 0.7)',
                points: 'rgba(0, 0, 0, 1)'
            },
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.createCanvas();
        this.setupEventListeners();
        console.log('🕷️ Spider minimal initialisé');
    }
    
    createCanvas() {
        this.container.innerHTML = `
            <canvas id="spider-canvas" width="${this.options.size}" height="${this.options.size}"></canvas>
        `;
        
        this.canvas = this.container.querySelector('#spider-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Haute résolution
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = this.options.size * dpr;
        this.canvas.height = this.options.size * dpr;
        this.canvas.style.width = `${this.options.size}px`;
        this.canvas.style.height = `${this.options.size}px`;
        this.ctx.scale(dpr, dpr);
        
        this.center = {
            x: this.options.size / 2,
            y: this.options.size / 2
        };
        this.radius = this.options.size * 0.32;
    }
    
    setupEventListeners() {
        // Animation au hover
        this.canvas.addEventListener('mouseenter', () => {
            this.canvas.style.opacity = '1';
        });
        
        this.canvas.addEventListener('mouseleave', () => {
            this.canvas.style.opacity = '0.9';
        });
    }
    
    setData(newData, animate = true) {
        if (!newData) return;
        
        this.data = this.normalizeData(newData);
        
        if (animate && !this.isAnimating) {
            this.animateToNewData();
        } else {
            this.animatedData = {...this.data};
            this.render();
        }
    }
    
    normalizeData(data) {
        const normalized = {};
        
        // Mapper les clés reçues aux catégories affichées
        this.options.categories.forEach(cat => {
            normalized[cat] = data[cat] || 0;
        });
        
        return normalized;
    }
    
    animateToNewData() {
        this.isAnimating = true;
        const duration = 800;
        const startTime = Date.now();
        const startData = {...this.animatedData};
        
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = this.easeInOutCubic(progress);
            
            // Interpoler
            this.options.categories.forEach(cat => {
                const start = startData[cat] || 0;
                const end = this.data[cat] || 0;
                this.animatedData[cat] = start + (end - start) * eased;
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
        return t < 0.5 
            ? 4 * t * t * t 
            : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }
    
    render() {
        const ctx = this.ctx;
        const center = this.center;
        const radius = this.radius;
        
        // Clear
        ctx.clearRect(0, 0, this.options.size, this.options.size);
        
        // Background
        ctx.fillStyle = this.options.colors.background;
        ctx.fillRect(0, 0, this.options.size, this.options.size);
        
        // Grille
        this.drawGrid(ctx, center, radius);
        
        // Axes
        this.drawRadialAxes(ctx, center, radius);
        
        // Données
        if (this.animatedData && Object.keys(this.animatedData).length > 0) {
            this.drawSpiderData(ctx, center, radius);
        }
        
        // Labels
        this.drawLabels(ctx, center, radius);
    }
    
    drawGrid(ctx, center, radius) {
        ctx.strokeStyle = this.options.colors.grid;
        ctx.lineWidth = 1;
        
        // Cercles concentriques (4 niveaux)
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
            const angle = i * angleStep - Math.PI / 2;
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
        
        // Forme remplie
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
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    drawLabels(ctx, center, radius) {
        const categories = this.options.categories;
        const angleStep = (Math.PI * 2) / categories.length;
        
        ctx.fillStyle = this.options.colors.text;
        ctx.font = '10px -apple-system, BlinkMacSystemFont, sans-serif';
        ctx.textAlign = 'center';
        
        for (let i = 0; i < categories.length; i++) {
            const angle = i * angleStep - Math.PI / 2;
            const labelDistance = radius + 20;
            
            const x = center.x + Math.cos(angle) * labelDistance;
            const y = center.y + Math.sin(angle) * labelDistance;
            
            // Ajuster alignement selon position
            if (Math.cos(angle) < -0.1) {
                ctx.textAlign = 'right';
            } else if (Math.cos(angle) > 0.1) {
                ctx.textAlign = 'left';
            } else {
                ctx.textAlign = 'center';
            }
            
            // Label
            ctx.fillText(categories[i], x, y + 4);
        }
    }
    
    clear() {
        this.data = null;
        this.animatedData = {};
        this.render();
    }
}
