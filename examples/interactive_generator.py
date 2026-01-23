#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur interactif pour le système Mix-Play
Permet de tester facilement différentes phrases et paramètres
"""

import sys
from pathlib import Path
from datetime import datetime
import re

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from mix_player import MixPlayer

class InteractiveMixGenerator:
    """Générateur interactif pour compositions Mix-Play"""
    
    def __init__(self):
        self.mix_player = MixPlayer()
        self.output_dir = Path("output_mix_play")
        self.output_dir.mkdir(exist_ok=True)
        
        print("🎵 Initialisation du Mix-Player...")
        self.mix_player.load_transcriptions()
        print("✅ Prêt pour la génération !")
        print()
    
    def show_menu(self):
        """Affiche le menu principal"""
        print("🎛️ GÉNÉRATEUR INTERACTIF MIX-PLAY")
        print("=" * 40)
        print("1. 🎯 Composition personnalisée")
        print("2. 🧪 Test avec phrases prédéfinies") 
        print("3. 🔍 Explorateur de vocabulaire")
        print("4. 🎨 Génération avec effets avancés")
        print("5. ⚖️ Comparaison avec/sans diversification")
        print("6. 📊 Analyse de phrases multiples")
        print("q. Quitter")
        print("-" * 40)
    
    def custom_composition(self):
        """Composition personnalisée avec phrase utilisateur"""
        print("\n🎯 COMPOSITION PERSONNALISÉE")
        print("-" * 25)
        
        phrase = input("🎤 Entrez votre phrase : ").strip()
        if not phrase:
            print("❌ Phrase vide")
            return
        
        print(f"🎵 Phrase : {phrase}")
        
        # Options
        print("\n⚙️ Options :")
        diversify = input("  Diversifier les sources ? (O/n) : ").strip().lower() not in ['n', 'non', 'no']
        confidence = float(input("  Seuil de confiance (0.0-1.0) [0.4] : ") or "0.4")
        
        # Nettoyage et composition
        words = re.findall(r'\b\w+\b', phrase.lower())
        composed = self.mix_player.compose_sentence(
            words, 
            prioritize_diversity=diversify,
            min_confidence=confidence
        )
        
        if not composed.words:
            print("❌ Aucun mot trouvé dans cette phrase")
            return
        
        # Génération audio
        self._generate_audio(composed, f"custom_{datetime.now().strftime('%H%M%S')}")
    
    def test_predefined_phrases(self):
        """Test avec phrases prédéfinies intéressantes"""
        print("\n🧪 PHRASES DE TEST PRÉDÉFINIES")
        print("-" * 30)
        
        test_phrases = [
            "avec tout mon amour je te dis bonjour",
            "la vie est belle comme une chanson",
            "je vois la lumière dans tes yeux",
            "avec avec avec tout tout tout amour amour",  # Test répétitions
            "bonjour comment allez vous aujourd hui",
            "la la la musique de de de notre vie",  # Test diversification
            "je suis là pour toi mon amour"
        ]
        
        print("📝 Phrases disponibles :")
        for i, phrase in enumerate(test_phrases, 1):
            print(f"  {i}. {phrase}")
        
        try:
            choice = int(input("\n🔢 Choisir une phrase (1-7) : ")) - 1
            if 0 <= choice < len(test_phrases):
                phrase = test_phrases[choice]
                print(f"🎯 Phrase sélectionnée : {phrase}")
                
                words = re.findall(r'\b\w+\b', phrase.lower())
                composed = self.mix_player.compose_sentence(
                    words, 
                    prioritize_diversity=True,
                    min_confidence=0.3
                )
                
                if composed.words:
                    self._generate_audio(composed, f"predefined_{choice+1}")
                else:
                    print("❌ Aucun mot trouvé")
            else:
                print("❌ Choix invalide")
        except ValueError:
            print("❌ Numéro invalide")
    
    def explore_vocabulary(self):
        """Exploration interactive du vocabulaire"""
        print("\n🔍 EXPLORATEUR DE VOCABULAIRE")
        print("-" * 28)
        
        while True:
            word = input("🔎 Mot à rechercher (ou 'retour') : ").strip()
            if word.lower() in ['retour', 'back', 'q']:
                break
            
            if not word:
                continue
            
            matches = self.mix_player.search_word(word, max_results=5)
            if matches:
                print(f"✅ '{word}' trouvé - {len(matches)} correspondances :")
                for i, match in enumerate(matches, 1):
                    print(f"  {i}. {match.word} - {Path(match.file_name).stem} - {match.speaker}")
            else:
                print(f"❌ '{word}' non trouvé")
                
                # Suggestions
                import difflib
                similar = difflib.get_close_matches(
                    self.mix_player.clean_word(word),
                    self.mix_player.word_index.keys(),
                    n=3, cutoff=0.6
                )
                if similar:
                    print(f"💡 Suggestions : {', '.join(similar)}")
            print()
    
    def advanced_effects_generation(self):
        """Génération avec effets audio avancés"""
        print("\n🎨 GÉNÉRATION AVEC EFFETS AVANCÉS")
        print("-" * 32)
        
        phrase = input("🎤 Phrase pour les effets : ").strip()
        if not phrase:
            return
        
        words = re.findall(r'\b\w+\b', phrase.lower())
        composed = self.mix_player.compose_sentence(
            words, 
            prioritize_diversity=True,
            min_confidence=0.3
        )
        
        if not composed.words:
            print("❌ Aucun mot trouvé")
            return
        
        # Différents effets
        effects = [
            {"name": "Standard", "fade_mode": "standard", "tempo": 1.0},
            {"name": "Artistique", "fade_mode": "artistic", "tempo": 1.0},
            {"name": "Fluide", "fade_mode": "seamless", "tempo": 1.0},
            {"name": "Lent Dramatique", "fade_mode": "artistic", "tempo": 0.7},
            {"name": "Rapide Énergique", "fade_mode": "standard", "tempo": 1.3}
        ]
        
        print(f"\n🎬 Génération de {len(effects)} versions avec effets...")
        
        for effect in effects:
            try:
                filename = f"effect_{effect['name'].lower().replace(' ', '_')}"
                audio_file = self.mix_player.generate_mixed_audio(
                    composed,
                    str(self.output_dir / f"{filename}.mp3"),
                    fade_mode=effect['fade_mode'],
                    tempo_factor=effect['tempo'],
                    word_padding=0.1
                )
                print(f"✅ {effect['name']} : {Path(audio_file).name}")
            except Exception as e:
                print(f"❌ Erreur {effect['name']} : {e}")
    
    def compare_diversity(self):
        """Comparaison avec/sans diversification"""
        print("\n⚖️ COMPARAISON DIVERSIFICATION")
        print("-" * 30)
        
        phrase = input("🎤 Phrase à comparer : ").strip()
        if not phrase:
            return
        
        words = re.findall(r'\b\w+\b', phrase.lower())
        
        print("\n🌟 Avec diversification :")
        composed_div = self.mix_player.compose_sentence(
            words, prioritize_diversity=True, min_confidence=0.3
        )
        
        print("\n🔄 Sans diversification :")
        composed_std = self.mix_player.compose_sentence(
            words, prioritize_diversity=False, min_confidence=0.3
        )
        
        if composed_div.words:
            self._generate_audio(composed_div, "avec_diversification")
        if composed_std.words:
            self._generate_audio(composed_std, "sans_diversification")
    
    def analyze_multiple_phrases(self):
        """Analyse de plusieurs phrases en batch"""
        print("\n📊 ANALYSE MULTIPLE")
        print("-" * 20)
        
        phrases = []
        print("📝 Entrez les phrases (ligne vide pour terminer) :")
        
        while True:
            phrase = input(f"{len(phrases)+1:2d}. ").strip()
            if not phrase:
                break
            phrases.append(phrase)
        
        if not phrases:
            return
        
        print(f"\n🔄 Analyse de {len(phrases)} phrases...")
        
        for i, phrase in enumerate(phrases, 1):
            print(f"\n--- PHRASE {i} : {phrase} ---")
            words = re.findall(r'\b\w+\b', phrase.lower())
            composed = self.mix_player.compose_sentence(
                words, prioritize_diversity=True, min_confidence=0.3
            )
            
            if composed.words:
                self._generate_audio(composed, f"batch_{i:02d}")
    
    def _generate_audio(self, composed, filename_prefix):
        """Génère l'audio pour une composition"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.mp3"
        
        try:
            audio_file = self.mix_player.generate_mixed_audio(
                composed,
                str(self.output_dir / filename),
                fade_mode="artistic",
                word_padding=0.1,
                tempo_factor=1.0,
                prioritize_diversity=True
            )
            print(f"✅ Audio généré : {Path(audio_file).name}")
            
            # Proposer écoute sur macOS
            import platform
            if platform.system() == "Darwin":
                listen = input("🎧 Écouter maintenant ? (O/n) : ").strip().lower()
                if listen not in ['n', 'non', 'no']:
                    try:
                        import subprocess
                        subprocess.run(["afplay", audio_file])
                    except Exception as e:
                        print(f"⚠️ Erreur lecture : {e}")
        
        except Exception as e:
            print(f"❌ Erreur génération : {e}")
    
    def run(self):
        """Lance le générateur interactif"""
        while True:
            self.show_menu()
            choice = input("👉 Choix : ").strip().lower()
            
            if choice == 'q' or choice == 'quit':
                print("👋 Au revoir !")
                break
            elif choice == '1':
                self.custom_composition()
            elif choice == '2':
                self.test_predefined_phrases()
            elif choice == '3':
                self.explore_vocabulary()
            elif choice == '4':
                self.advanced_effects_generation()
            elif choice == '5':
                self.compare_diversity()
            elif choice == '6':
                self.analyze_multiple_phrases()
            else:
                print("❌ Choix invalide")
            
            input("\n⏎ Appuyez sur Entrée pour continuer...")
            print("\n" + "="*50 + "\n")

def quick_test():
    """Test rapide avec quelques phrases"""
    print("⚡ MODE TEST RAPIDE")
    print("-" * 20)
    
    generator = InteractiveMixGenerator()
    
    test_phrases = [
        "bonjour comment allez vous",
        "je vous souhaite une belle journée",
        "avec tout mon amour"
    ]
    
    for i, phrase in enumerate(test_phrases, 1):
        print(f"\n🧪 Test {i}: {phrase}")
        words = re.findall(r'\b\w+\b', phrase.lower())
        composed = generator.mix_player.compose_sentence(
            words, prioritize_diversity=True, min_confidence=0.3
        )
        
        if composed.words:
            generator._generate_audio(composed, f"quick_test_{i}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_test()
    else:
        generator = InteractiveMixGenerator()
        generator.run()