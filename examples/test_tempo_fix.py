"""
Test spécifique du changement de tempo corrigé.
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer


def test_tempo_correction():
    """Test spécifique du changement de tempo."""
    
    print("🎵 Test du Changement de Tempo (Corrigé)")
    print("=" * 45)
    
    # Initialiser
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    # Phrase courte
    test_phrase = "bonjour"
    
    print(f"🎯 Mot de test: {test_phrase}")
    
    # Composer
    composed = mix_player.compose_sentence([test_phrase], min_confidence=0.7)
    
    if not composed.words:
        print("❌ Mot non trouvé")
        return
    
    print(f"✅ Trouvé: {composed.text}")
    print(f"🎭 Locuteur: {composed.speakers_used[0]}")
    print()
    
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Tests de tempo
    tempo_tests = [
        {"factor": 1.0, "name": "Normal"},
        {"factor": 0.8, "name": "Ralenti 20%"},
        {"factor": 0.6, "name": "Ralenti 40%"},
        {"factor": 1.2, "name": "Accéléré 20%"}
    ]
    
    for test in tempo_tests:
        factor = test["factor"]
        name = test["name"]
        
        output_file = f"output_mix_play/tempo_test_{name.lower().replace(' ', '_').replace('%', 'pct')}_{timestamp}.mp3"
        
        print(f"🎵 Test {name} (x{factor})...")
        
        try:
            audio_file = mix_player.generate_mixed_audio(
                composed,
                output_file,
                fade_mode="standard",
                word_padding=0.15,
                tempo_factor=factor,
                preserve_pitch=True,
                gap_duration=0.2
            )
            
            print(f"   ✅ Généré: {Path(audio_file).name}")
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            continue
        
        # Écouter immédiatement pour vérifier
        listen = input(f"   🎧 Écouter {name} maintenant ? (O/n): ").strip().lower()
        if listen not in ['n', 'non', 'no']:
            try:
                import subprocess
                import platform
                if platform.system() == "Darwin":
                    subprocess.run(["afplay", audio_file])
                    
                    # Vérifier la qualité
                    quality = input("   🎯 Qualité OK ? (bruit/distorsion ?) (O/n): ").strip().lower()
                    if quality in ['n', 'non', 'no']:
                        print("   ⚠️ Problème détecté avec ce tempo")
                    else:
                        print("   ✅ Tempo fonctionnel")
                        
            except Exception as e:
                print(f"   ⚠️ Erreur lecture: {e}")
        
        print()
    
    print("💡 RÉSUMÉ DES CORRECTIONS:")
    print("• Utilisation de fichiers temporaires WAV")
    print("• Import/export avec librosa + soundfile")
    print("• Gestion robuste des erreurs")
    print("• Préservation du pitch avec time_stretch")


if __name__ == "__main__":
    test_tempo_correction()