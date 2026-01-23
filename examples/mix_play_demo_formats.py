"""
Exemple Mix-Play amélioré avec génération de différents formats et ouverture automatique.

Cet exemple génère à la fois MP3 et WAV, et ouvre automatiquement les résultats.
"""

import sys
from pathlib import Path
from datetime import datetime
import subprocess
import platform

# Ajouter le répertoire src au path
sys.path.append(str(Path(__file__).parent / "src"))

from mix_player import MixPlayer


def open_file_or_folder(path):
    """Ouvre un fichier ou dossier selon l'OS."""
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(path)])
        elif system == "Windows":
            subprocess.run(["start", str(path)], shell=True)
        else:  # Linux
            subprocess.run(["xdg-open", str(path)])
        print(f"📂 Ouvert: {path}")
    except Exception as e:
        print(f"⚠️  Impossible d'ouvrir automatiquement: {e}")
        print(f"📂 Vous pouvez ouvrir manuellement: {path}")


def main():
    """Exemple Mix-Play avec génération multi-formats."""
    
    print("🎵 Mix-Play - Exemple Multi-Formats")
    print("=" * 40)
    
    # Phrase à composer
    target_sentence = "avec tout mon amour et bonheur"
    
    print(f"📝 Phrase à composer: {target_sentence}")
    print()
    
    # Initialiser
    mix_player = MixPlayer()
    mix_player.load_transcriptions()
    
    # Composer la phrase
    print("🎭 Composition de la phrase...")
    words = target_sentence.split()
    composed = mix_player.compose_sentence(
        words=words,
        min_confidence=0.4
    )
    
    print(f"✅ Phrase composée: {composed.text}")
    print(f"🔤 Mots trouvés: {len(composed.words)}/{len(words)}")
    print()
    
    if not composed.words:
        print("❌ Aucun mot trouvé, arrêt du traitement")
        return
    
    # Créer les noms de fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output_mix_play")
    base_name = f"demo_multi_format_{timestamp}"
    
    mp3_file = output_dir / f"{base_name}.mp3"
    wav_file = output_dir / f"{base_name}.wav"
    info_file = output_dir / f"{base_name}_info.json"
    
    print("🎬 GÉNÉRATION DES FICHIERS")
    print("-" * 30)
    
    # Générer MP3
    print("🎵 Génération MP3...")
    try:
        audio_mp3 = mix_player.generate_mixed_audio(
            composed,
            str(mp3_file),
            gap_duration=0.2,
            crossfade_duration=30
        )
        print(f"✅ MP3 généré: {mp3_file}")
    except Exception as e:
        print(f"❌ Erreur MP3: {e}")
        return
    
    # Générer WAV (conversion depuis le MP3)
    print("🎵 Génération WAV...")
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_mp3(str(mp3_file))
        audio.export(str(wav_file), format="wav")
        print(f"✅ WAV généré: {wav_file}")
    except Exception as e:
        print(f"❌ Erreur WAV: {e}")
    
    # Exporter les informations
    print("📄 Export des informations...")
    try:
        info_exported = mix_player.export_composed_sentence_info(composed, str(info_file))
        print(f"✅ Infos générées: {info_file}")
    except Exception as e:
        print(f"❌ Erreur infos: {e}")
    
    print()
    print("🎉 GÉNÉRATION TERMINÉE")
    print("=" * 25)
    
    # Afficher les détails
    print("📊 DÉTAILS DE LA COMPOSITION:")
    print(f"• Texte final: {composed.text}")
    print(f"• Durée totale: {composed.total_duration:.2f}s")
    print(f"• Intervenants: {', '.join(composed.speakers_used)}")
    print(f"• Fichiers source: {', '.join(Path(f).stem for f in composed.files_used)}")
    print()
    
    print("📁 FICHIERS GÉNÉRÉS:")
    if mp3_file.exists():
        size_mp3 = mp3_file.stat().st_size
        print(f"• MP3: {mp3_file} ({size_mp3:,} octets)")
    
    if wav_file.exists():
        size_wav = wav_file.stat().st_size
        print(f"• WAV: {wav_file} ({size_wav:,} octets)")
    
    if info_file.exists():
        size_info = info_file.stat().st_size
        print(f"• JSON: {info_file} ({size_info:,} octets)")
    
    print()
    
    # Proposer d'ouvrir les fichiers
    response = input("🎧 Ouvrir le dossier des résultats ? (O/n): ").strip().lower()
    
    if response not in ['n', 'non', 'no']:
        open_file_or_folder(output_dir)
    
    # Proposer de lire le fichier audio directement
    if platform.system() == "Darwin":  # macOS
        response = input("🎵 Lire le fichier MP3 maintenant ? (O/n): ").strip().lower()
        if response not in ['n', 'non', 'no'] and mp3_file.exists():
            try:
                subprocess.run(["afplay", str(mp3_file)])
            except Exception as e:
                print(f"⚠️  Impossible de lire automatiquement: {e}")
    
    print()
    print("💡 CONSEILS:")
    print("• Vous pouvez double-cliquer sur le MP3 pour l'écouter")
    print("• Le fichier WAV est compatible avec tous les lecteurs")
    print("• Le fichier JSON contient tous les détails de la composition")
    print("• Essayez d'autres phrases avec vocabulary_explorer.py")


if __name__ == "__main__":
    main()