#!/usr/bin/env python3
"""
Script de test pour les trois fichiers audio avec optimisation GPU.
Lance automatiquement la transcription de tous les fichiers présents.
"""

import sys
import os
from pathlib import Path
import torch

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcriber import AudioTranscriber
from export import ExportManager


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
    else:
        print("❌ CUDA non disponible")
    
    # MPS (Apple Silicon)
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print("✅ MPS (Metal Performance Shaders) disponible - GPU Apple Silicon")
        return "mps"
    else:
        print("❌ MPS non disponible")
    
    if torch.cuda.is_available():
        return "cuda"
    else:
        return "cpu"


def test_transcription_with_gpu():
    """Test de transcription avec optimisation GPU."""
    print("🎵 Test de Transcription Audio avec GPU")
    print("=" * 50)
    
    # Vérifier les dispositifs
    optimal_device = check_gpu_availability()
    print(f"\n🎯 Dispositif optimal détecté : {optimal_device}")
    
    # Dossiers
    audio_dir = Path("../audio")
    output_dir = Path("../output")
    output_dir.mkdir(exist_ok=True)
    
    # Lister les fichiers audio
    audio_files = list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.wav"))
    
    if not audio_files:
        print("❌ Aucun fichier audio trouvé dans le dossier 'audio/'")
        return
    
    print(f"\n📁 {len(audio_files)} fichier(s) audio trouvé(s) :")
    for f in audio_files:
        print(f"   - {f.name}")
    
    # Initialiser le transcripteur avec GPU
    print(f"\n🚀 Initialisation du transcripteur (modèle: medium, device: {optimal_device})")
    transcriber = AudioTranscriber(
        model_name="medium",
        language="fr", 
        device=optimal_device,
        verbose=True
    )
    
    export_manager = ExportManager()
    
    # Traiter chaque fichier
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n" + "="*60)
        print(f"🎵 TRANSCRIPTION {i}/{len(audio_files)}: {audio_file.name}")
        print(f"📱 Dispositif actuel : {transcriber.actual_device}")
        print("="*60)
        
        try:
            # Transcription
            result = transcriber.transcribe_with_timestamps(
                str(audio_file), 
                word_timestamps=True
            )
            
            # Nom de fichier de sortie basé sur le nom d'entrée
            base_name = audio_file.stem.replace(" ", "_").lower()
            
            # Export JSON complet
            json_output = output_dir / f"{base_name}_full.json"
            export_manager.export_json(result, str(json_output))
            
            # Export CSV pour analyse
            csv_output = output_dir / f"{base_name}_data.csv"
            export_manager.export_csv(result, str(csv_output))
            
            # Export format artistique
            artistic_output = output_dir / f"{base_name}_artistic.json"
            export_manager.export_artistic_format(result, str(artistic_output))
            
            # Export sous-titres
            srt_output = output_dir / f"{base_name}_subtitles.srt"
            export_manager.export_srt_subtitles(result, str(srt_output))
            
            # Statistiques
            duration = result["metadata"]["duration"]
            word_count = sum(len(seg["words"]) for seg in result["transcription"]["segments"])
            segments_count = len(result["transcription"]["segments"])
            
            print(f"\n📊 RÉSULTATS POUR {audio_file.name}:")
            print(f"   ⏱️  Durée audio : {duration:.2f}s")
            print(f"   🎬 Segments : {segments_count}")
            print(f"   🔤 Mots totaux : {word_count}")
            print(f"   📈 Mots/minute : {(word_count/duration)*60:.1f}")
            print(f"   📄 Fichiers générés :")
            print(f"      - {json_output.name} (JSON complet)")
            print(f"      - {csv_output.name} (données tabulaires)")
            print(f"      - {artistic_output.name} (format artistique)")
            print(f"      - {srt_output.name} (sous-titres)")
            
            # Aperçu du texte
            text_preview = result["transcription"]["text"][:100]
            print(f"   📝 Aperçu : {text_preview}{'...' if len(result['transcription']['text']) > 100 else ''}")
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {audio_file.name} : {str(e)}")
            continue
    
    print(f"\n✨ TRANSCRIPTION TERMINÉE !")
    print(f"📂 Tous les résultats sont dans le dossier : {output_dir.absolute()}")
    
    # Résumé des fichiers de sortie
    output_files = list(output_dir.glob("*"))
    if output_files:
        print(f"\n📋 {len(output_files)} fichier(s) de sortie généré(s) :")
        for f in sorted(output_files):
            size_kb = f.stat().st_size / 1024
            print(f"   - {f.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    test_transcription_with_gpu()