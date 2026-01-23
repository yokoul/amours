#!/usr/bin/env python3
"""
Script de test simplifié pour les trois fichiers audio sans détection d'intervenants.
Version stable qui fonctionne de manière fiable.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcriber import AudioTranscriber
from export import ExportManager


def test_simple_transcription():
    """Lance les tests de transcription de base."""
    
    print("🎵 TEST DE TRANSCRIPTION AUDIO SIMPLIFIÉ")
    print("🚀 Version stable sans détection d'intervenants")
    print("=" * 70)
    
    # Créer le dossier de sortie
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Lister les fichiers audio disponibles
    audio_dir = Path("audio")
    audio_files = []
    
    # Rechercher tous les fichiers audio
    if audio_dir.exists():
        for file_path in audio_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']:
                audio_files.append(file_path)
    
    if not audio_files:
        print("❌ Aucun fichier audio trouvé dans le dossier 'audio/'")
        return
    
    print(f"🎵 Fichiers audio trouvés : {len(audio_files)}")
    for f in audio_files:
        print(f"   • {f.name}")
    
    print("\n" + "=" * 70)
    
    # Traiter chaque fichier
    results = []
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n🎵 FICHIER {i}/{len(audio_files)} : {audio_file.name}")
        print("=" * 70)
        
        try:
            # Initialiser le transcripteur (CPU seulement pour stabilité)
            transcriber = AudioTranscriber(
                model_name="medium",
                language="fr",
                device="cpu",  # CPU pour éviter les problèmes MPS
                verbose=False
            )
            
            # Transcription
            print("🔄 Transcription en cours...")
            result = transcriber.transcribe_with_timestamps(
                str(audio_file),
                word_timestamps=True
            )
            
            # Générer un nom de fichier de sortie propre
            output_name = audio_file.stem.lower().replace(" ", "_")
            
            # Export
            export_manager = ExportManager()
            
            # JSON complet
            json_file = output_dir / f"{output_name}_complete.json"
            export_manager.export_json(result, str(json_file))
            
            # CSV pour analyse
            csv_file = output_dir / f"{output_name}_data.csv"
            export_manager.export_csv(result, str(csv_file))
            
            # Format artistique
            artistic_file = output_dir / f"{output_name}_artistic.json"
            export_manager.export_artistic_format(result, str(artistic_file))
            
            # Sous-titres
            srt_file = output_dir / f"{output_name}_subtitles.srt"
            export_manager.export_srt_subtitles(result, str(srt_file))
            
            # Mots uniquement (format simple)
            words_file = output_dir / f"{output_name}_words.json"
            export_manager.export_words_only(result, str(words_file))
            
            # Statistiques
            print_stats(result)
            
            results.append((audio_file.name, result))
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {audio_file.name} : {e}")
            import traceback
            traceback.print_exc()
    
    # Résumé final
    print_final_summary(results)


def print_stats(result):
    """Affiche les statistiques de transcription."""
    metadata = result["metadata"]
    segments = result["transcription"]["segments"]
    
    print(f"\n📊 STATISTIQUES :")
    print(f"   ⏱️  Durée : {metadata['duration']:.2f}s")
    print(f"   🎬 Segments : {len(segments)}")
    
    # Compter les mots
    total_words = sum(len(seg.get("words", [])) for seg in segments)
    if total_words > 0:
        wpm = total_words / metadata['duration'] * 60
        print(f"   🔤 Mots : {total_words} ({wpm:.1f} mots/min)")
        
        # Quelques exemples de mots avec timecodes
        print(f"   📝 Aperçu des premiers mots :")
        word_count = 0
        for seg in segments[:2]:  # Premiers segments
            for word in seg.get("words", [])[:5]:  # 5 premiers mots
                print(f"      '{word['word']}' ({word['start']:.2f}s-{word['end']:.2f}s)")
                word_count += 1
                if word_count >= 10:
                    break
            if word_count >= 10:
                break


def print_final_summary(results):
    """Affiche le résumé final."""
    print(f"\n{'='*70}")
    print(f"📋 RÉSUMÉ FINAL")
    print(f"{'='*70}")
    
    if not results:
        print("❌ Aucun fichier traité avec succès")
        return
    
    print(f"✅ Fichiers traités avec succès : {len(results)}")
    
    total_duration = sum(r[1]["metadata"]["duration"] for _, r in results)
    total_segments = sum(len(r[1]["transcription"]["segments"]) for _, r in results)
    total_words = sum(
        sum(len(seg.get("words", [])) for seg in r[1]["transcription"]["segments"])
        for _, r in results
    )
    
    print(f"⏱️  Durée totale analysée : {total_duration:.1f}s")
    print(f"🎬 Segments totaux : {total_segments}")
    print(f"🔤 Mots totaux : {total_words}")
    
    if total_duration > 0:
        avg_wpm = total_words / total_duration * 60
        print(f"📈 Débit moyen global : {avg_wpm:.1f} mots/min")
    
    print(f"\n📁 Fichiers générés dans 'output/' :")
    print(f"   • JSON complets avec métadonnées détaillées")
    print(f"   • CSV pour analyse de données et statistiques")
    print(f"   • Formats artistiques optimisés pour créations")
    print(f"   • Sous-titres SRT pour intégration vidéo")
    print(f"   • Listes de mots avec timecodes précis")
    
    print(f"\n🎨 Données prêtes pour exploitation artistique !")
    print(f"💡 Chaque mot a ses timecodes précis pour synchronisation")
    print(f"{'='*70}")


def main():
    """Fonction principale."""
    test_simple_transcription()


if __name__ == "__main__":
    main()