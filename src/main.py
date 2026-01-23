"""
Module principal pour la transcription audio avec timecodes.
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
        description="Transcription audio avec timecodes précis"
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
        choices=["cpu", "cuda", "mps", "auto"],
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
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Dispositif de calcul (auto: détection automatique)"
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
    print("=" * 50)
    
    try:
        # Initialiser le transcripteur
        transcriber = AudioTranscriber(
            model_name=args.model,
            language=args.language,
            device=args.device if args.device != "auto" else None,
            verbose=args.verbose
        )
        
        # Effectuer la transcription
        print("🔄 Transcription en cours...")
        result = transcriber.transcribe_with_timestamps(
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
        
        # Afficher quelques statistiques
        duration = result["metadata"]["duration"]
        word_count = sum(len(segment["words"]) for segment in result["transcription"]["segments"])
        print(f"⏱️  Durée audio : {duration:.2f}s")
        print(f"🔤 Nombre de mots : {word_count}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la transcription : {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()