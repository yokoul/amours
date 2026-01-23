"""
Test des nouvelles fonctionnalités audio : fondu artistique et contrôle du tempo.

Ce script teste les différents modes de fondu et les ajustements de tempo
pour créer des rendus plus artistiques et contrôlés.
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer


def test_advanced_audio_features():
    """Test les nouvelles fonctionnalités audio avancées."""
    
    print("🎨 Test des Fonctionnalités Audio Avancées")
    print("=" * 45)
    
    # Initialiser
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    # Phrase de test courte pour bien entendre les effets
    test_phrase = "avec tout cet amour, je vois le bonheur comme une mélodie"
    
    print(f"🎯 Phrase de test: {test_phrase}")
    print()
    
    # Composer la phrase avec diversification des sources
    import re
    words = re.findall(r'\b\w+\b', test_phrase.lower())  # Nettoyer la ponctuation
    
    composed = mix_player.compose_sentence(
        words,
        min_confidence=0.3,  # Seuil plus bas pour plus de résultats
        prioritize_diversity=True  # Activer la diversification des sources
    )
    
    if not composed.words:
        print("❌ Aucun mot trouvé pour cette phrase")
        return
    
    print(f"✅ Composition: {composed.text}")
    print(f"🔤 {len(composed.words)} mots trouvés")
    print()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output_mix_play")
    
    # Tests des différents modes
    test_configs = [
        {
            "name": "Standard",
            "params": {
                "fade_mode": "standard",
                "word_padding": 0.1,
                "tempo_factor": 1.0,
                "gap_duration": 0.3,
                "crossfade_duration": 50
            }
        },
        {
            "name": "Artistique (Fondu Long)",
            "params": {
                "fade_mode": "artistic",
                "word_padding": 0.05,  # Moins de padding, plus de fondu
                "tempo_factor": 1.0,
                "gap_duration": 0.2,
                "crossfade_duration": 150
            }
        },
        {
            "name": "Seamless (Fondu Court)",
            "params": {
                "fade_mode": "seamless",
                "word_padding": 0.02,  # Très peu de padding
                "tempo_factor": 1.0,
                "gap_duration": 0.1,
                "crossfade_duration": 30
            }
        },
        {
            "name": "Tempo Ralenti (0.7x)",
            "params": {
                "fade_mode": "artistic",
                "word_padding": 0.1,
                "tempo_factor": 0.7,  # Plus lent
                "preserve_pitch": True,
                "gap_duration": 0.2,
                "crossfade_duration": 100
            }
        },
        {
            "name": "Tempo Très Lent (0.5x)",
            "params": {
                "fade_mode": "seamless",
                "word_padding": 0.05,
                "tempo_factor": 0.5,  # Beaucoup plus lent
                "preserve_pitch": True,
                "gap_duration": 0.15,
                "crossfade_duration": 80
            }
        },
        {
            "name": "Tempo Accéléré (1.3x)",
            "params": {
                "fade_mode": "standard",
                "word_padding": 0.1,
                "tempo_factor": 1.3,  # Plus rapide
                "preserve_pitch": True,
                "gap_duration": 0.25,
                "crossfade_duration": 40
            }
        }
    ]
    
    generated_files = []
    
    print("🎬 GÉNÉRATION DES VERSIONS DE TEST")
    print("-" * 35)
    
    for i, config in enumerate(test_configs, 1):
        print(f"\n{i}️⃣ Test: {config['name']}")
        
        # Nom de fichier sécurisé
        safe_name = config['name'].lower().replace(' ', '_').replace('(', '').replace(')', '')
        output_file = output_dir / f"advanced_{safe_name}_{timestamp}.mp3"
        
        try:
            audio_file = mix_player.generate_mixed_audio(
                composed,
                str(output_file),
                **config['params']
            )
            
            generated_files.append((config['name'], audio_file))
            print(f"✅ Généré: {Path(audio_file).name}")
            
        except Exception as e:
            print(f"❌ Erreur pour {config['name']}: {e}")
    
    print(f"\n🎧 ÉCOUTE COMPARATIVE")
    print("-" * 25)
    print(f"{len(generated_files)} versions générées:")
    
    for name, file_path in generated_files:
        print(f"• {name}: {Path(file_path).name}")
    
    print(f"\n💡 CONSEILS D'ÉCOUTE:")
    print("• Standard: Référence classique")
    print("• Artistique: Fondus longs, effet 'rêveur'")
    print("• Seamless: Transitions minimales, plus 'parlé'")
    print("• Tempo Ralenti: Plus de compréhension, effet dramatique")
    print("• Tempo Très Lent: Effet hypnotique, chaque mot distinct")
    print("• Tempo Accéléré: Plus dynamique, effet énergique")
    
    # Proposer d'écouter chaque version
    print(f"\n🎵 ÉCOUTE INTERACTIVE")
    print("-" * 20)
    
    for name, file_path in generated_files:
        if Path(file_path).exists():
            response = input(f"Écouter '{name}' ? (O/n/q pour quitter): ").strip().lower()
            
            if response == 'q':
                break
            elif response not in ['n', 'non', 'no']:
                try:
                    import subprocess
                    import platform
                    
                    if platform.system() == "Darwin":  # macOS
                        subprocess.run(["afplay", file_path])
                        print("✅ Lecture terminée")
                    else:
                        print(f"📂 Ouvrez manuellement: {file_path}")
                        
                except Exception as e:
                    print(f"⚠️ Erreur de lecture: {e}")
            print()
    
    print("🎨 RECOMMANDATIONS D'USAGE:")
    print("• Fondu artistique: Idéal pour créations poétiques/rêveuses")
    print("• Fondu seamless: Parfait pour narration naturelle")  
    print("• Tempo ralenti: Excellent pour compréhension/drama")
    print("• Combinaisons: Mélangez les modes selon l'effet souhaité")


def test_librosa_availability():
    """Teste si librosa est disponible pour les changements de tempo."""
    try:
        import librosa
        print("✅ librosa disponible - Contrôle du tempo activé")
        return True
    except ImportError:
        print("⚠️ librosa non installé")
        print("📦 Pour activer le contrôle du tempo: pip install librosa")
        print("🎵 Les tests de tempo seront ignorés")
        return False


if __name__ == "__main__":
    print("🔍 Vérification des dépendances...")
    librosa_available = test_librosa_availability()
    print()
    
    if not librosa_available:
        install = input("Installer librosa maintenant ? (O/n): ").strip().lower()
        if install not in ['n', 'non', 'no']:
            import subprocess
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "librosa"], check=True)
                print("✅ librosa installé avec succès")
            except subprocess.CalledProcessError:
                print("❌ Échec de l'installation de librosa")
    
    test_advanced_audio_features()