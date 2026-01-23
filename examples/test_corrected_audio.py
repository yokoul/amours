"""
Test corrigé des fonctionnalités audio avancées.
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer


def test_corrected_audio():
    """Test des corrections audio."""
    
    print("🔧 Test des Corrections Audio")
    print("=" * 35)
    
    # Initialiser
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    # Phrase courte pour les tests
    test_phrase = "avec tout cet amour, je vois le bonheur comme une mélodie"
    
    print(f"🎯 Phrase: {test_phrase}")
    
    # Composer
    composed = mix_player.compose_sentence(test_phrase.split(), min_confidence=0.6)
    
    if not composed.words:
        print("❌ Aucun mot trouvé")
        return
    
    print(f"✅ {composed.text}")
    print()
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Tests des corrections
    tests = [
        {
            "name": "Standard (référence)",
            "params": {
                "fade_mode": "standard",
                "word_padding": 0.15,
                "tempo_factor": 1.0,
                "gap_duration": 0.3
            }
        },
        {
            "name": "Fondu Artistique Long",
            "params": {
                "fade_mode": "artistic",
                "word_padding": 0.1,
                "tempo_factor": 1.0,
                "gap_duration": 0.25,
                "crossfade_duration": 500  # Très long
            }
        },
        {
            "name": "Sans Changement Tempo", 
            "params": {
                "fade_mode": "standard", 
                "word_padding": 0.15,
                "tempo_factor": 1.0  # Pas de changement
            }
        }
    ]
    
    generated_files = []
    
    for test in tests:
        safe_name = test['name'].lower().replace(' ', '_').replace('(', '').replace(')', '')
        output_file = f"output_mix_play/corrected_{safe_name}_{timestamp}.mp3"
        
        print(f"🎵 {test['name']}...")
        
        try:
            audio_file = mix_player.generate_mixed_audio(
                composed,
                output_file,
                **test['params']
            )
            
            generated_files.append((test['name'], audio_file))
            print(f"   ✅ Généré: {Path(audio_file).name}")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        print()
    
    # Écoute
    print("🎧 ÉCOUTE DES CORRECTIONS:")
    for name, file_path in generated_files:
        if Path(file_path).exists():
            listen = input(f"Écouter '{name}' ? (O/n/q): ").strip().lower()
            if listen == 'q':
                break
            elif listen not in ['n', 'non', 'no']:
                try:
                    import subprocess
                    import platform
                    if platform.system() == "Darwin":
                        subprocess.run(["afplay", file_path])
                        print("✅ Terminé")
                except Exception as e:
                    print(f"⚠️ Erreur lecture: {e}")
            print()
    
    print("💡 Corrections apportées:")
    print("• Tempo: Méthode par fichiers temporaires (plus robuste)")
    print("• Fondu artistique: Augmenté à 300-500ms")
    print("• Mode seamless: Réduit à 15ms (supprimé des tests)")


def check_dependencies():
    """Vérifie les dépendances pour le tempo."""
    missing = []
    
    try:
        import librosa
        print("✅ librosa disponible")
    except ImportError:
        missing.append("librosa")
    
    try:
        import soundfile
        print("✅ soundfile disponible")
    except ImportError:
        missing.append("soundfile")
    
    if missing:
        print(f"⚠️ Dépendances manquantes: {', '.join(missing)}")
        print(f"📦 Installation: pip install {' '.join(missing)}")
        return False
    
    return True


if __name__ == "__main__":
    print("🔍 Vérification des dépendances...")
    deps_ok = check_dependencies()
    print()
    
    if not deps_ok:
        install = input("Installer les dépendances manquantes ? (O/n): ").strip().lower()
        if install not in ['n', 'non', 'no']:
            import subprocess
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "librosa", "soundfile"], check=True)
                print("✅ Dépendances installées")
            except:
                print("❌ Échec installation")
    
    test_corrected_audio()