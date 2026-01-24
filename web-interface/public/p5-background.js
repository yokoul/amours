// Arrière-plan artistique P5.js pour le spectacle d'amour
let particles = [];
let emotions = [];
let heartBeats = [];
let currentIntensity = 0.3;

function setup() {
    let canvas = createCanvas(windowWidth, windowHeight);
    canvas.parent('p5-container');
    
    // Initialiser les particules d'amour
    for (let i = 0; i < 50; i++) {
        particles.push(new LoveParticle(random(width), random(height)));
    }
    
    // Émotions flottantes
    for (let i = 0; i < 8; i++) {
        emotions.push(new EmotionWave(random(width), random(height)));
    }
    
    // Battements de cœur
    for (let i = 0; i < 3; i++) {
        heartBeats.push(new HeartBeat(random(width * 0.2, width * 0.8), random(height * 0.2, height * 0.8)));
    }
}

function draw() {
    // Fond gradient dynamique
    for (let i = 0; i <= height; i++) {
        let inter = map(i, 0, height, 0, 1);
        let c = lerpColor(color(102, 126, 234, 50), color(118, 75, 162, 50), inter);
        stroke(c);
        line(0, i, width, i);
    }
    
    // Particules d'amour
    for (let particle of particles) {
        particle.update();
        particle.display();
    }
    
    // Ondes d'émotion
    for (let emotion of emotions) {
        emotion.update();
        emotion.display();
    }
    
    // Battements de cœur
    for (let heartBeat of heartBeats) {
        heartBeat.update();
        heartBeat.display();
    }
    
    // Effet de pulsation générale
    drawPulse();
}

function windowResized() {
    resizeCanvas(windowWidth, windowHeight);
}

// Classe particule d'amour
class LoveParticle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.vx = random(-1, 1);
        this.vy = random(-1, 1);
        this.size = random(2, 8);
        this.alpha = random(100, 200);
        this.color = color(random(200, 255), random(100, 200), random(150, 255), this.alpha);
        this.life = 1;
    }
    
    update() {
        this.x += this.vx * currentIntensity;
        this.y += this.vy * currentIntensity;
        
        // Mouvement organique
        this.x += sin(frameCount * 0.01 + this.x * 0.01) * 0.5;
        this.y += cos(frameCount * 0.01 + this.y * 0.01) * 0.5;
        
        // Rebonds sur les bords
        if (this.x < 0 || this.x > width) this.vx *= -1;
        if (this.y < 0 || this.y > height) this.vy *= -1;
        
        this.x = constrain(this.x, 0, width);
        this.y = constrain(this.y, 0, height);
        
        // Variation de l'alpha
        this.alpha = 150 + sin(frameCount * 0.02 + this.x * 0.01) * 50;
    }
    
    display() {
        push();
        fill(red(this.color), green(this.color), blue(this.color), this.alpha);
        noStroke();
        
        // Forme de cœur stylisée ou cercle
        if (random() < 0.3) {
            // Mini cœur
            this.drawHeart(this.x, this.y, this.size);
        } else {
            // Particule circulaire avec effet de lueur
            for (let r = this.size; r > 0; r -= 1) {
                fill(red(this.color), green(this.color), blue(this.color), this.alpha / (this.size - r + 1));
                ellipse(this.x, this.y, r * 2);
            }
        }
        pop();
    }
    
    drawHeart(x, y, s) {
        beginShape();
        vertex(x, y + s/2);
        bezierVertex(x - s/2, y - s/2, x - s, y + s/3, x, y + s);
        bezierVertex(x + s, y + s/3, x + s/2, y - s/2, x, y + s/2);
        endShape();
    }
}

// Classe onde d'émotion
class EmotionWave {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.radius = 0;
        this.maxRadius = random(100, 200);
        this.speed = random(1, 3);
        this.alpha = 100;
        this.color = color(255, random(150, 255), random(150, 255));
        this.growing = true;
    }
    
    update() {
        if (this.growing) {
            this.radius += this.speed;
            this.alpha = map(this.radius, 0, this.maxRadius, 100, 0);
            
            if (this.radius >= this.maxRadius) {
                this.growing = false;
                // Redémarrer à une nouvelle position
                setTimeout(() => {
                    this.x = random(width);
                    this.y = random(height);
                    this.radius = 0;
                    this.growing = true;
                    this.maxRadius = random(100, 200);
                }, random(2000, 5000));
            }
        }
    }
    
    display() {
        if (this.growing && this.alpha > 0) {
            push();
            stroke(red(this.color), green(this.color), blue(this.color), this.alpha);
            strokeWeight(2);
            noFill();
            ellipse(this.x, this.y, this.radius * 2);
            
            // Onde concentrique
            if (this.radius > 20) {
                stroke(red(this.color), green(this.color), blue(this.color), this.alpha * 0.5);
                ellipse(this.x, this.y, (this.radius - 20) * 2);
            }
            pop();
        }
    }
}

// Classe battement de cœur
class HeartBeat {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.size = 20;
        this.beatPhase = 0;
        this.baseSize = 20;
        this.beatSpeed = 0.1;
    }
    
    update() {
        this.beatPhase += this.beatSpeed;
        this.size = this.baseSize + sin(this.beatPhase) * 10 * currentIntensity;
    }
    
    display() {
        push();
        fill(255, 100, 150, 150 + sin(this.beatPhase) * 50);
        noStroke();
        this.drawHeart(this.x, this.y, this.size);
        
        // Effet de lueur
        fill(255, 150, 200, 50);
        this.drawHeart(this.x, this.y, this.size * 1.5);
        pop();
    }
    
    drawHeart(x, y, s) {
        beginShape();
        vertex(x, y + s/4);
        bezierVertex(x - s/2, y - s/2, x - s, y + s/6, x, y + s/2);
        bezierVertex(x + s, y + s/6, x + s/2, y - s/2, x, y + s/4);
        endShape();
    }
}

// Fonction pour effet de pulsation générale
function drawPulse() {
    let pulseIntensity = sin(frameCount * 0.05) * 0.3 + 0.7;
    
    push();
    fill(255, 255, 255, pulseIntensity * 10);
    noStroke();
    rect(0, 0, width, height);
    pop();
}

// Fonction pour augmenter l'intensité lors d'interactions
function increaseIntensity() {
    currentIntensity = min(currentIntensity + 0.2, 1.0);
    
    // Ajouter des particules temporaires
    for (let i = 0; i < 10; i++) {
        particles.push(new LoveParticle(mouseX || random(width), mouseY || random(height)));
    }
    
    // Limiter le nombre de particules
    if (particles.length > 100) {
        particles.splice(0, particles.length - 100);
    }
    
    // Retour progressif à la normale
    setTimeout(() => {
        currentIntensity = max(currentIntensity - 0.1, 0.3);
    }, 2000);
}

// Fonction appelée depuis l'interface principale
function onWordSelected() {
    increaseIntensity();
}

function onPhraseGenerated() {
    currentIntensity = 1.0;
    
    // Explosion de particules
    for (let i = 0; i < 30; i++) {
        particles.push(new LoveParticle(width/2 + random(-100, 100), height/2 + random(-100, 100)));
    }
    
    // Nouvelles ondes d'émotion
    for (let i = 0; i < 3; i++) {
        emotions.push(new EmotionWave(random(width), random(height)));
    }
}

// Exposition des fonctions globalement
window.onWordSelected = onWordSelected;
window.onPhraseGenerated = onPhraseGenerated;