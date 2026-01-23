#!/usr/bin/env python3
"""
Script de test avec détection d'intervenants simplifiée et stable.
Utilise une méthode acoustique pour identifier les différents locuteurs.
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from simple_transcriber_with_speakers import SimpleAudioTranscriberWithSpeakers
from export import ExportManager


def test_with_simple_speakers():
    """Test avec détection d'intervenants simplifiée."""
    
    print("🎵 TEST DE TRANSCRIPTION AVEC DÉTECTION D'INTERVENANTS")
    print("🚀 Version stable avec clustering acoustique")
    print("=" * 70)
    
    # Créer le dossier de sortie
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Lister les fichiers audio
    audio_dir = Path("audio")
    audio_files = []
    
    if audio_dir.exists():
        for file_path in audio_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']:
                audio_files.append(file_path)
    
    if not audio_files:
        print("❌ Aucun fichier audio trouvé")
        return
    
    print(f"🎵 Fichiers trouvés : {len(audio_files)}")
    for f in audio_files:
        print(f"   • {f.name}")
    
    print("\n" + "=" * 70)
    
    # Traitement
    results = []
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n🎵 FICHIER {i}/{len(audio_files)} : {audio_file.name}")
        print("=" * 70)
        
        try:
            # Transcripteur avec détection d'intervenants
            transcriber = SimpleAudioTranscriberWithSpeakers(
                model_name="medium",
                language="fr",
                enable_speaker_detection=True
            )
            
            # Transcription
            result = transcriber.transcribe_with_simple_speakers(
                str(audio_file),
                word_timestamps=True
            )
            
            # Nom de fichier propre
            output_name = audio_file.stem.lower().replace(" ", "_").replace("par", "par")
            
            # Export
            export_manager = ExportManager()
            
            # JSON complet avec intervenants
            json_file = output_dir / f"{output_name}_with_speakers_complete.json"
            export_manager.export_json(result, str(json_file))
            
            # CSV avec informations d'intervenants
            csv_file = output_dir / f"{output_name}_with_speakers_data.csv"
            export_manager.export_csv(result, str(csv_file))
            
            # Format artistique avec intervenants
            artistic_file = output_dir / f"{output_name}_with_speakers_artistic.json"
            export_manager.export_artistic_format(result, str(artistic_file))
            
            # Sous-titres avec intervenants
            srt_file = output_dir / f"{output_name}_with_speakers_subtitles.srt"
            export_srt_with_speakers(result, str(srt_file))
            
            # Statistiques détaillées
            print_detailed_stats(result)
            
            results.append((audio_file.name, result))
            
        except Exception as e:
            print(f"❌ Erreur : {e}")
            import traceback
            traceback.print_exc()
    
    # Résumé final
    print_final_summary(results)


def export_srt_with_speakers(transcription_data, output_path):
    """Export SRT avec indication des intervenants."""
    try:
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds % 1) * 1000)
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(transcription_data["transcription"]["segments"], 1):
                start_time = format_time(segment["start"])
                end_time = format_time(segment["end"])
                speaker = segment.get("speaker", "Inconnu")
                text = segment["text"].strip()
                
                # Ajouter le nom de l'intervenant
                if speaker and speaker != "Inconnu":
                    text = f"[{speaker}] {text}"
                
                f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
        
        print(f"📺 Sous-titres avec intervenants : {Path(output_path).name}")
        
    except Exception as e:
        print(f"❌ Erreur export SRT : {e}")


def print_detailed_stats(result):
    """Affiche les statistiques détaillées."""
    metadata = result["metadata"]
    speakers = result["speakers"]
    segments = result["transcription"]["segments"]
    
    print(f"\n📊 STATISTIQUES DÉTAILLÉES")
    print(f"{'─'*50}")
    
    print(f"🎵 Fichier : {metadata['file']}")
    print(f"⏱️  Durée : {metadata['duration']:.2f}s")
    print(f"🎬 Segments : {len(segments)}")
    print(f"🔬 Méthode de détection : {metadata.get('detection_method', 'N/A')}")
    
    # Intervenants
    print(f"\n👥 INTERVENANTS ({len(speakers)}) :")
    if speakers:
        for speaker_id, info in speakers.items():
            percentage = (info['total_time'] / metadata['duration']) * 100
            print(f"   • {speaker_id}:")
            print(f"     - Temps de parole : {info['total_time']:.1f}s ({percentage:.1f}%)")
            if 'segments_count' in info:
                print(f"     - Interventions : {info['segments_count']}")
    
    # Distribution des mots par intervenant
    total_words = sum(len(seg.get("words", [])) for seg in segments)
    if total_words > 0:
        print(f"\n🔤 RÉPARTITION DES MOTS :")
        print(f"   • Total : {total_words}")
        
        speaker_words = {}
        for segment in segments:
            speaker = segment.get("speaker", "Inconnu")
            word_count = len(segment.get("words", []))
            speaker_words[speaker] = speaker_words.get(speaker, 0) + word_count
        
        for speaker, count in speaker_words.items():
            percentage = (count / total_words) * 100
            print(f"   • {speaker} : {count} mots ({percentage:.1f}%)")


def print_final_summary(results):
    """Résumé final."""
    print(f"\n{'='*70}")
    print(f"📋 RÉSUMÉ FINAL AVEC INTERVENANTS")
    print(f"{'='*70}")
    
    if not results:
        print("❌ Aucun fichier traité")
        return
    
    print(f"✅ Fichiers traités : {len(results)}")
    
    # Correction de l'accès aux données des résultats
    total_duration = sum(result["metadata"]["duration"] for _, result in results)
    total_speakers = sum(len(result["speakers"]) for _, result in results)
    total_words = sum(
        sum(len(seg.get("words", [])) for seg in result["transcription"]["segments"])
        for _, result in results
    )
    
    print(f"⏱️  Durée totale : {total_duration:.1f}s")
    print(f"👥 Total d'intervenants détectés : {total_speakers}")
    print(f"🔤 Mots totaux : {total_words}")
    
    print(f"\n📁 Fichiers générés avec intervenants :")
    print(f"   • JSON complets avec attribution des locuteurs")
    print(f"   • CSV avec colonnes speaker pour chaque mot")
    print(f"   • Sous-titres SRT avec [Intervenant_X] devant chaque segment")
    print(f"   • Formats artistiques avec analyse par intervenant")
    
    print(f"\n🎨 Données prêtes pour exploitation artistique avec intervenants !")
    print(f"💡 Chaque mot est attribué à son intervenant avec timecodes précis")
    print(f"{'='*70}")


def main():
    """Fonction principale."""
    # Installer scikit-learn si pas disponible
    try:
        import sklearn
        print("✅ scikit-learn disponible pour clustering")
    except ImportError:
        print("⚠️  scikit-learn non disponible - utilisation méthode basique")
        print("💡 Pour améliorer la détection : pip install scikit-learn")
    
    test_with_simple_speakers()


if __name__ == "__main__":
    main()