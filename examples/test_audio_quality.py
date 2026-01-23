"""
Test de qualité audio pour le Mix-Play.

Cet exemple teste différentes configurations pour améliorer la qualité audio.
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer


def test_audio_quality():
    """Test différentes configurations de qualité audio."""
    
    print("🔊 Test de Qualité Audio Mix-Play")
    print("=" * 40)
    
    # Initialiser
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    # Phrases de test (mots courants et courts)
    test_phrases = [
        "avec tout mon amour",
        "la vie est belle",
        "bonjour et merci",
        "dans le monde"
    ]
    
    print("🎯 Phrases de test:")
    for i, phrase in enumerate(test_phrases, 1):
        print(f"{i}. {phrase}")
    print()
    
    # Laisser l'utilisateur choisir
    while True:
        try:
            choice = int(input(f"Choisissez une phrase (1-{len(test_phrases)}): ")) - 1
            if 0 <= choice < len(test_phrases):
                selected_phrase = test_phrases[choice]
                break
            else:
                print("❌ Choix invalide")
        except ValueError:
            print("❌ Veuillez entrer un nombre")
    
    print(f"\n📝 Phrase sélectionnée: {selected_phrase}")
    
    # Composer la phrase
    words = selected_phrase.split()
    composed = mix_player.compose_sentence(
        words=words,
        min_confidence=0.6  # Qualité raisonnable
    )
    
    if not composed.words:
        print("❌ Aucun mot trouvé pour cette phrase")
        return
    
    print(f"✅ Composition: {composed.text}")
    print(f"🔤 {len(composed.words)}/{len(words)} mots trouvés")
    
    # Détails des mots trouvés
    print(f"\n🎭 DÉTAILS DES MOTS:")
    for i, word in enumerate(composed.words, 1):
        duration_ms = word.duration * 1000
        print(f"{i}. '{word.word.strip()}' - {word.speaker}")
        print(f"   ⏱️  {word.start:.2f}s - {word.end:.2f}s ({duration_ms:.0f}ms)")
        print(f"   🎯 Confiance: {word.confidence:.1%}")
        print(f"   📁 Source: {Path(word.file_name).stem}")
    
    print(f"\n🎬 TESTS DE GÉNÉRATION AUDIO")
    print("-" * 30)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output_mix_play")
    
    # Test 1: Configuration par défaut
    print("1️⃣ Test avec configuration par défaut...")
    try:
        audio1 = mix_player.generate_mixed_audio(
            composed,
            str(output_dir / f"test_default_{timestamp}.mp3"),
            gap_duration=0.3,
            crossfade_duration=50,
            word_padding=0.1
        )
        print(f"✅ Généré: {audio1}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 2: Plus de padding pour plus de contexte
    print(f"\n2️⃣ Test avec plus de contexte (padding 0.3s)...")
    try:
        audio2 = mix_player.generate_mixed_audio(
            composed,
            str(output_dir / f"test_contextual_{timestamp}.mp3"),
            gap_duration=0.2,
            crossfade_duration=30,
            word_padding=0.3  # Plus de contexte
        )
        print(f"✅ Généré: {audio2}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Transitions douces
    print(f"\n3️⃣ Test avec transitions douces...")
    try:
        audio3 = mix_player.generate_mixed_audio(
            composed,
            str(output_dir / f"test_smooth_{timestamp}.mp3"),
            gap_duration=0.1,  # Moins d'espace
            crossfade_duration=100,  # Plus de crossfade
            word_padding=0.2,
            normalize_volume=True
        )
        print(f"✅ Généré: {audio3}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print(f"\n🎧 ÉCOUTE DES RÉSULTATS")
    print("-" * 25)
    print("Trois versions ont été générées:")
    print("• test_default: Configuration standard")
    print("• test_contextual: Plus de contexte autour des mots")  
    print("• test_smooth: Transitions plus douces")
    print()
    
    # Proposer d'écouter chaque version
    for test_name in ["default", "contextual", "smooth"]:
        file_path = output_dir / f"test_{test_name}_{timestamp}.mp3"
        if file_path.exists():
            response = input(f"🎵 Écouter test_{test_name} ? (O/n): ").strip().lower()
            if response not in ['n', 'non', 'no']:
                try:
                    import subprocess
                    import platform
                    if platform.system() == "Darwin":  # macOS
                        subprocess.run(["afplay", str(file_path)])
                        print("✅ Lecture terminée")
                    else:
                        print(f"📂 Ouvrez manuellement: {file_path}")
                except Exception as e:
                    print(f"⚠️ Erreur de lecture: {e}")
            print()
    
    print("💡 CONSEILS POUR AMÉLIORER LA QUALITÉ:")
    print("• Utilisez des mots plus courts et courants")
    print("• Préférez les mots avec une confiance > 80%")
    print("• Ajustez le padding selon le contexte nécessaire")
    print("• Les transitions douces aident mais peuvent créer des artefacts")
    print("• Testez avec des intervenants similaires (même sexe, même âge)")


if __name__ == "__main__":
    test_audio_quality()