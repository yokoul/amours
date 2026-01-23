#!/usr/bin/env python3
"""
Script de test pour les trois fichiers audio avec optimisation GPU et détection d'intervenants.
Lance automatiquement la transcription de tous les fichiers avec analyse des intervenants.
"""

import sys
import os
from pathlib import Path
import torch

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_gpu_availability():
    """Vérifie la disponibilité des GPU."""
    print("🔍 Vérification des dispositifs disponibles :")
    
    # PyTorch version
    print(f"📦 PyTorch version : {torch.__version__}")
    
    # CPU
    print("✅ CPU disponible")
    
    # CUDA (NVIDIA)
    if torch.cuda.is_available():
        print(f"✅ CUDA disponible - {torch.cuda.device_count()} GPU(s)")
        for i in range(torch.cuda.device_count()):
            print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
        return "cuda"
    else:
        print("❌ CUDA non disponible")
    
    # MPS (Apple Silicon)
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print("✅ MPS (Metal Performance Shaders) disponible - GPU Apple Silicon")
        return "mps"
    else:
        print("❌ MPS non disponible")
    
    return "cpu"


def install_missing_dependencies():
    """Installe les dépendances manquantes pour la détection d'intervenants."""
    print("📦 Vérification des dépendances...")
    
    try:
        import pyannote.audio
        print("✅ pyannote.audio disponible")
        return True
    except ImportError:
        print("⚠️  pyannote.audio non disponible")
        print("💡 Installation recommandée : pip install pyannote.audio")
        
        # Continuer sans détection d'intervenants
        return False


def test_transcription_with_gpu():
    """Lance les tests de transcription avec optimisation GPU."""
    
    # Vérifier la disponibilité du GPU
    optimal_device = check_gpu_availability()
    
    # Vérifier les dépendances
    diarization_available = install_missing_dependencies()
    
    print(f"\n🚀 Configuration de test :")
    print(f"   • Dispositif optimal : {optimal_device}")
    print(f"   • Détection d'intervenants : {'Oui' if diarization_available else 'Non (continuer sans)'}")
    print("=" * 70)
    
    # Créer le dossier de sortie
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Lister les fichiers audio disponibles
    audio_dir = Path("audio")  # Chemin depuis la racine du projet
    audio_files = []
    
    # Rechercher tous les fichiers audio, y compris ceux avec des espaces
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
    
    # Importer les modules après vérification
    try:
        if diarization_available:
            from transcriber_with_speakers import AudioTranscriberWithSpeakers as Transcriber
            transcribe_method = "transcribe_with_speakers"
        else:
            from transcriber import AudioTranscriber as Transcriber
            transcribe_method = "transcribe_with_timestamps"
        
        from export import ExportManager
        
    except ImportError as e:
        print(f"❌ Erreur d'import : {e}")
        return
    
    # Traiter chaque fichier
    results = []
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n🎵 FICHIER {i}/{len(audio_files)} : {audio_file.name}")
        print("=" * 70)
        
        try:
            # Initialiser le transcripteur
            if diarization_available:
                transcriber = Transcriber(
                    model_name="medium",
                    language="fr", 
                    device=optimal_device if optimal_device != "cpu" else None,
                    enable_diarization=True,
                    verbose=False
                )
            else:
                transcriber = Transcriber(
                    model_name="medium",
                    language="fr",
                    device=optimal_device if optimal_device != "cpu" else None,
                    verbose=False  
                )
            
            # Transcription
            print("🔄 Transcription en cours...")
            
            if diarization_available:
                result = transcriber.transcribe_with_speakers(
                    str(audio_file),
                    word_timestamps=True
                )
            else:
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
            if diarization_available:
                export_srt_with_speakers(result, str(srt_file))
            else:
                export_manager.export_srt_subtitles(result, str(srt_file))
            
            # Statistiques
            print_stats(result, diarization_available)
            
            results.append((audio_file.name, result))
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {audio_file.name} : {e}")
            import traceback
            traceback.print_exc()
    
    # Résumé final
    print_final_summary(results, diarization_available)


def export_srt_with_speakers(transcription_data, output_path):
    """Exporte SRT avec indication des intervenants."""
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
                speaker = segment.get("speaker", "")
                text = segment["text"].strip()
                
                if speaker and speaker != "Inconnu":
                    text = f"[{speaker}] {text}"
                
                f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
        
        print(f"📺 Sous-titres avec intervenants : {Path(output_path).name}")
        
    except Exception as e:
        print(f"❌ Erreur export SRT : {e}")


def print_stats(result, with_speakers=False):
    """Affiche les statistiques de transcription."""
    metadata = result["metadata"]
    segments = result["transcription"]["segments"]
    
    print(f"\n📊 STATISTIQUES :")
    print(f"   ⏱️  Durée : {metadata['duration']:.2f}s")
    print(f"   🖥️  Dispositif : {metadata.get('device', 'N/A')}")
    print(f"   🎬 Segments : {len(segments)}")
    
    if with_speakers and "speakers" in result:
        speakers = result["speakers"]
        print(f"   👥 Intervenants : {len(speakers)}")
        
        if speakers:
            for speaker_id, info in speakers.items():
                percentage = (info['total_time'] / metadata['duration']) * 100
                print(f"      • {speaker_id}: {info['total_time']:.1f}s ({percentage:.1f}%)")
    
    # Compter les mots
    total_words = sum(len(seg.get("words", [])) for seg in segments)
    if total_words > 0:
        wpm = total_words / metadata['duration'] * 60
        print(f"   🔤 Mots : {total_words} ({wpm:.1f} mots/min)")


def print_final_summary(results, with_speakers=False):
    """Affiche le résumé final."""
    print(f"\n{'='*70}")
    print(f"📋 RÉSUMÉ FINAL")
    print(f"{'='*70}")
    
    if not results:
        print("❌ Aucun fichier traité avec succès")
        return
    
    print(f"✅ Fichiers traités : {len(results)}")
    
    total_duration = sum(r[1]["metadata"]["duration"] for _, r in results)
    total_segments = sum(len(r[1]["transcription"]["segments"]) for _, r in results)
    
    print(f"⏱️  Durée totale : {total_duration:.1f}s")
    print(f"🎬 Segments totaux : {total_segments}")
    
    if with_speakers:
        total_speakers = sum(len(r[1].get("speakers", {})) for _, r in results)
        print(f"👥 Intervenants détectés : {total_speakers}")
    
    print(f"\n📁 Fichiers générés dans 'output/' :")
    print(f"   • JSON complets avec métadonnées")
    print(f"   • CSV pour analyse de données")
    print(f"   • Formats artistiques optimisés") 
    print(f"   • Sous-titres SRT {'avec intervenants' if with_speakers else ''}")
    
    print(f"\n🎨 Données prêtes pour exploitation artistique !")
    print(f"{'='*70}")


def main():
    """Fonction principale."""
    print("🎵 TEST DE TRANSCRIPTION AUDIO OPTIMISÉ")
    print("🚀 GPU + Détection d'intervenants + Export multi-formats")
    print("=" * 70)
    
    test_transcription_with_gpu()


if __name__ == "__main__":
    main()