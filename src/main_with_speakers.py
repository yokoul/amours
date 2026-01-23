"""
Module principal pour la transcription audio avec timecodes et détection d'intervenants.
Point d'entrée en ligne de commande pour le projet.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from transcriber_with_speakers import AudioTranscriberWithSpeakers
from export import ExportManager


def main():
    """Fonction principale du programme."""
    parser = argparse.ArgumentParser(
        description="Transcription audio avec timecodes précis et détection d'intervenants"
    )
    
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Chemin vers le fichier audio à transcrire"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Chemin de sortie pour les résultats (JSON ou CSV)"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="medium",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Modèle Whisper à utiliser (défaut: medium)"
    )
    
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="fr",
        help="Langue de l'audio (défaut: fr pour français)"
    )
    
    parser.add_argument(
        "--device", "-d",
        type=str,
        default=None,
        choices=["cpu", "cuda", "mps"],
        help="Dispositif de calcul (auto-détection par défaut)"
    )
    
    parser.add_argument(
        "--disable-diarization",
        action="store_true",
        help="Désactiver la détection d'intervenants"
    )
    
    parser.add_argument(
        "--word-timestamps",
        action="store_true",
        default=True,
        help="Inclure les timecodes au niveau des mots"
    )
    
    parser.add_argument(
        "--format", "-f",
        type=str,
        default="json",
        choices=["json", "csv"],
        help="Format de sortie (défaut: json)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Affichage détaillé du processus"
    )
    
    args = parser.parse_args()
    
    # Vérifier que le fichier d'entrée existe
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Erreur : Le fichier {input_path} n'existe pas.")
        sys.exit(1)
    
    # Créer le dossier de sortie si nécessaire
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🎵 Transcription de : {input_path}")
    print(f"📝 Modèle Whisper : {args.model}")
    print(f"🌍 Langue : {args.language}")
    print(f"🖥️  Dispositif : {args.device or 'auto-détection'}")
    print(f"👥 Détection d'intervenants : {'Non' if args.disable_diarization else 'Oui'}")
    print(f"⏱️  Timecodes des mots : {'Oui' if args.word_timestamps else 'Non'}")
    print("=" * 70)
    
    try:
        # Initialiser le transcripteur avec détection d'intervenants
        transcriber = AudioTranscriberWithSpeakers(
            model_name=args.model,
            language=args.language,
            device=args.device,
            enable_diarization=not args.disable_diarization,
            verbose=args.verbose
        )
        
        # Effectuer la transcription avec détection d'intervenants
        print("🔄 Transcription et analyse des intervenants en cours...")
        result = transcriber.transcribe_with_speakers(
            str(input_path),
            word_timestamps=args.word_timestamps
        )
        
        # Exporter les résultats
        print("💾 Export des résultats...")
        export_manager = ExportManager()
        
        if args.format == "json":
            export_manager.export_json(result, str(output_path))
        else:
            export_manager.export_csv(result, str(output_path))
        
        print(f"✅ Transcription terminée !")
        print(f"📄 Résultats sauvegardés : {output_path}")
        
        # Afficher les statistiques détaillées
        metadata = result["metadata"]
        speakers = result["speakers"]
        segments = result["transcription"]["segments"]
        
        print("=" * 70)
        print("📊 STATISTIQUES")
        print(f"⏱️  Durée audio : {metadata['duration']:.2f}s")
        print(f"🎬 Segments de transcription : {len(segments)}")
        print(f"👥 Intervenants détectés : {len(speakers)}")
        
        if speakers:
            print("\n👤 INTERVENANTS :")
            for speaker_id, speaker_info in speakers.items():
                print(f"   • {speaker_id}: {speaker_info['total_time']:.1f}s "
                      f"({speaker_info['segments_count']} segments)")
        
        # Compter les mots
        total_words = sum(len(seg.get("words", [])) for seg in segments)
        if total_words > 0:
            print(f"🔤 Nombre total de mots : {total_words}")
            print(f"📈 Débit moyen : {total_words / metadata['duration'] * 60:.1f} mots/min")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Erreur lors de la transcription : {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()