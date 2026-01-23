"""
Interface Mix-Play Finale - Combine mots individuels et chunks.

Cette interface permet de choisir entre différentes stratégies de composition
et d'ajuster les paramètres pour obtenir le meilleur résultat.
"""

import sys
from pathlib import Path
from datetime import datetime
import subprocess
import platform
from typing import Dict

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer
sys.path.append(str(Path(__file__).parent / "examples"))
from chunk_mix_player import ChunkMixPlayer


class FinalMixPlayer:
    """Interface finale combinant toutes les approches."""
    
    def __init__(self):
        self.word_player = MixPlayer()
        self.chunk_player = ChunkMixPlayer()
        self.initialized = False
    
    def initialize(self):
        """Initialise les deux systèmes."""
        if self.initialized:
            return
        
        print("🚀 Initialisation des systèmes Mix-Play...")
        
        # Charger les transcriptions
        self.word_player.load_transcriptions()
        
        # Extraire les chunks (plus de variété)
        self.chunk_player.extract_chunks(
            min_chunk_size=2, 
            max_chunk_size=5,  # Chunks plus longs
            min_confidence=0.6  # Seuil plus bas pour plus de choix
        )
        
        self.initialized = True
        print("✅ Systèmes initialisés")
    
    def analyze_phrase(self, phrase: str) -> Dict:
        """Analyse une phrase et retourne les options disponibles."""
        self.initialize()
        
        words = phrase.split()
        analysis = {
            'phrase': phrase,
            'word_count': len(words),
            'strategies': {}
        }
        
        print(f"🔍 Analyse de: {phrase}")
        
        # Stratégie 1: Mots individuels haute qualité
        word_composition_hq = self.word_player.compose_sentence(
            words, min_confidence=0.8
        )
        analysis['strategies']['words_hq'] = {
            'name': 'Mots individuels (haute qualité)',
            'composition': word_composition_hq,
            'coverage': len(word_composition_hq.words) / len(words),
            'quality_score': sum(w.confidence for w in word_composition_hq.words) / max(1, len(word_composition_hq.words))
        }
        
        # Stratégie 2: Mots individuels couverture maximum
        word_composition_max = self.word_player.compose_sentence(
            words, min_confidence=0.5
        )
        analysis['strategies']['words_max'] = {
            'name': 'Mots individuels (couverture max)',
            'composition': word_composition_max,
            'coverage': len(word_composition_max.words) / len(words),
            'quality_score': sum(w.confidence for w in word_composition_max.words) / max(1, len(word_composition_max.words))
        }
        
        # Stratégie 3: Chunks
        chunk_composition = self.chunk_player.compose_from_chunks(phrase)
        analysis['strategies']['chunks'] = {
            'name': 'Groupes de mots (chunks)',
            'composition': chunk_composition,
            'coverage': len(chunk_composition.words) / len(words) if chunk_composition.words else 0,
            'quality_score': sum(w.confidence for w in chunk_composition.words) / max(1, len(chunk_composition.words))
        }
        
        # Recommandation
        best_strategy = max(
            analysis['strategies'].items(),
            key=lambda x: x[1]['coverage'] * 0.7 + x[1]['quality_score'] * 0.3
        )[0]
        analysis['recommended'] = best_strategy
        
        return analysis
    
    def display_analysis(self, analysis: Dict):
        """Affiche l'analyse des stratégies."""
        print(f"\n📊 ANALYSE: {analysis['phrase']}")
        print("=" * 50)
        
        for strategy_key, strategy_data in analysis['strategies'].items():
            composition = strategy_data['composition']
            print(f"\n{strategy_data['name']}:")
            print(f"  📝 Résultat: {composition.text}")
            print(f"  📈 Couverture: {strategy_data['coverage']:.1%}")
            print(f"  🎯 Qualité: {strategy_data['quality_score']:.1%}")
            print(f"  🎭 Locuteurs: {len(composition.speakers_used)}")
            print(f"  ⏱️  Durée: {composition.total_duration:.1f}s")
            
            if strategy_key == analysis['recommended']:
                print("  ⭐ RECOMMANDÉE")
        
        print(f"\n💡 Stratégie recommandée: {analysis['strategies'][analysis['recommended']]['name']}")
    
    def generate_comparison_audio(self, analysis: Dict, output_dir: str = "output_mix_play"):
        """Génère l'audio pour toutes les stratégies disponibles."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_phrase = "".join(c if c.isalnum() else "_" for c in analysis['phrase'])[:20]
        
        generated_files = []
        
        for strategy_key, strategy_data in analysis['strategies'].items():
            composition = strategy_data['composition']
            
            if not composition.words:
                print(f"⚠️ Pas de mots pour {strategy_data['name']}")
                continue
            
            output_file = f"{output_dir}/compare_{strategy_key}_{safe_phrase}_{timestamp}.mp3"
            
            try:
                if strategy_key == 'chunks':
                    audio_file = self.chunk_player.generate_chunk_audio(
                        composition, output_file,
                        gap_duration=0.15,
                        chunk_padding=0.15
                    )
                else:
                    audio_file = self.word_player.generate_mixed_audio(
                        composition, output_file,
                        gap_duration=0.2,
                        crossfade_duration=40,
                        word_padding=0.2,
                        normalize_volume=True,
                        fade_mode="standard"
                    )
                
                generated_files.append((strategy_data['name'], audio_file))
                print(f"✅ {strategy_data['name']}: {Path(audio_file).name}")
                
            except Exception as e:
                print(f"❌ Erreur pour {strategy_data['name']}: {e}")
        
        return generated_files
    
    def generate_advanced_audio(self, composition, phrase: str, output_dir: str = "output_mix_play"):
        """Génère plusieurs versions avec les nouvelles fonctionnalités audio."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_phrase = "".join(c if c.isalnum() else "_" for c in phrase)[:15]
        
        # Configurations avancées
        advanced_configs = [
            {
                "name": "Standard",
                "params": {"fade_mode": "standard", "word_padding": 0.15, "tempo_factor": 1.0}
            },
            {
                "name": "Artistique (Fondu Long)",
                "params": {"fade_mode": "artistic", "word_padding": 0.05, "tempo_factor": 1.0, 
                          "gap_duration": 0.2, "crossfade_duration": 150}
            },
            {
                "name": "Seamless (Fondu Court)", 
                "params": {"fade_mode": "seamless", "word_padding": 0.02, "tempo_factor": 1.0,
                          "gap_duration": 0.1, "crossfade_duration": 30}
            },
            {
                "name": "Tempo Ralenti",
                "params": {"fade_mode": "artistic", "word_padding": 0.1, "tempo_factor": 0.7,
                          "preserve_pitch": True, "gap_duration": 0.2}
            }
        ]
        
        generated_files = []
        
        for config in advanced_configs:
            safe_config_name = config['name'].lower().replace(' ', '_').replace('(', '').replace(')', '')
            output_file = f"{output_dir}/advanced_{safe_config_name}_{safe_phrase}_{timestamp}.mp3"
            
            try:
                audio_file = self.word_player.generate_mixed_audio(
                    composition,
                    output_file,
                    **config['params']
                )
                
                generated_files.append((config['name'], audio_file))
                print(f"✅ {config['name']}: {Path(audio_file).name}")
                
            except Exception as e:
                print(f"❌ Erreur {config['name']}: {e}")
        
        return generated_files
    
    def play_audio_file(self, file_path: str):
        """Lit un fichier audio selon l'OS."""
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", file_path], check=True)
            elif system == "Windows":
                subprocess.run(["start", file_path], shell=True, check=True)
            else:  # Linux
                subprocess.run(["paplay", file_path], check=True)
            return True
        except Exception as e:
            print(f"⚠️ Impossible de lire {Path(file_path).name}: {e}")
            return False


def interactive_final_mix():
    """Interface interactive finale."""
    
    print("🎵 MIX-PLAY FINAL - Compositeur Audio Intelligent")
    print("=" * 55)
    
    mixer = FinalMixPlayer()
    
    while True:
        print(f"\n🎛️ MENU PRINCIPAL")
        print("-" * 20)
        print("1. Composer et comparer les stratégies")
        print("2. Composition rapide (stratégie recommandée)")
        print("3. Test avec phrases prédéfinies")
        print("4. 🆕 Effets audio avancés (fondu/tempo)")
        print("5. Quitter")
        
        choice = input("\nVotre choix (1-4): ").strip()
        
        if choice == '1':
            # Composition complète avec comparaison
            phrase = input("\nPhrase à composer: ").strip()
            if not phrase:
                continue
            
            analysis = mixer.analyze_phrase(phrase)
            mixer.display_analysis(analysis)
            
            generate = input("\nGénérer les fichiers audio pour comparaison ? (O/n): ").strip().lower()
            if generate not in ['n', 'non', 'no']:
                print("\n🎬 Génération des fichiers...")
                files = mixer.generate_comparison_audio(analysis)
                
                print(f"\n🎧 ÉCOUTE COMPARATIVE:")
                for strategy_name, file_path in files:
                    listen = input(f"Écouter '{strategy_name}' ? (O/n): ").strip().lower()
                    if listen not in ['n', 'non', 'no']:
                        mixer.play_audio_file(file_path)
        
        elif choice == '2':
            # Composition rapide
            phrase = input("\nPhrase à composer: ").strip()
            if not phrase:
                continue
            
            analysis = mixer.analyze_phrase(phrase)
            recommended = analysis['recommended']
            composition = analysis['strategies'][recommended]['composition']
            
            print(f"✅ Stratégie recommandée: {analysis['strategies'][recommended]['name']}")
            print(f"📝 Résultat: {composition.text}")
            
            generate = input("\nGénérer l'audio ? (O/n): ").strip().lower()
            if generate not in ['n', 'non', 'no']:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_phrase = "".join(c if c.isalnum() else "_" for c in phrase)[:20]
                output_file = f"output_mix_play/final_{safe_phrase}_{timestamp}.mp3"
                
                try:
                    if recommended == 'chunks':
                        audio_file = mixer.chunk_player.generate_chunk_audio(
                            composition, output_file
                        )
                    else:
                        audio_file = mixer.word_player.generate_mixed_audio(
                            composition, output_file,
                            word_padding=0.2,
                            normalize_volume=True
                        )
                    
                    print(f"🎵 Audio généré: {Path(audio_file).name}")
                    
                    listen = input("Écouter maintenant ? (O/n): ").strip().lower()
                    if listen not in ['n', 'non', 'no']:
                        mixer.play_audio_file(audio_file)
                
                except Exception as e:
                    print(f"❌ Erreur: {e}")
        
        elif choice == '3':
            # Phrases prédéfinies
            test_phrases = [
                "bonjour et merci beaucoup",
                "la vie est belle",
                "avec tout mon amour",
                "dans ce monde",
                "je vous aime",
                "c'est vraiment formidable"
            ]
            
            print(f"\n🎯 PHRASES DE TEST:")
            for i, phrase in enumerate(test_phrases, 1):
                print(f"{i}. {phrase}")
            
            try:
                choice_phrase = int(input(f"\nChoisir une phrase (1-{len(test_phrases)}): ")) - 1
                if 0 <= choice_phrase < len(test_phrases):
                    selected = test_phrases[choice_phrase]
                    analysis = mixer.analyze_phrase(selected)
                    mixer.display_analysis(analysis)
                    
                    files = mixer.generate_comparison_audio(analysis)
                    print(f"\n🎵 {len(files)} fichiers générés pour comparaison")
            except (ValueError, IndexError):
                print("❌ Choix invalide")
        
        elif choice == '4':
            print("\n👋 Merci d'avoir utilisé Mix-Play !")
            break
        
        else:
            print("❌ Choix invalide")


if __name__ == "__main__":
    interactive_final_mix()