#!/usr/bin/env python3
"""
Script principal intégrant l'analyse d'amour dans la transcription avec intervenants.
Étend main_with_speakers.py avec la couche sémantique d'analyse d'amour.
"""

import sys
from pathlib import Path
import argparse
import time

# Ajouter le répertoire src au PATH
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from simple_transcriber_with_speakers import SimpleAudioTranscriberWithSpeakers
from enriched_export import EnrichedExportManager
from love_analyzer import LoveTypeAnalyzer


def main():
    """Fonction principale avec analyse d'amour intégrée."""
    parser = argparse.ArgumentParser(
        description='Transcription audio avec détection des intervenants et analyse d\'amour'
    )
    parser.add_argument(
        '--input', '-i', 
        type=str, 
        required=True,
        help='Chemin vers le fichier audio à transcrire'
    )
    parser.add_argument(
        '--output', '-o', 
        type=str, 
        default='output',
        help='Dossier de sortie (défaut: output)'
    )
    parser.add_argument(
        '--formats', '-f',
        nargs='+',
        choices=['json', 'csv', 'artistic', 'srt', 'summary'],
        default=['json', 'csv', 'artistic', 'srt', 'summary'],
        help='Formats d\'export à générer'
    )
    parser.add_argument(
        '--min-segment-length',
        type=float,
        default=0.5,
        help='Durée minimum des segments en secondes (défaut: 0.5)'
    )
    parser.add_argument(
        '--speaker-clustering',
        choices=['simple', 'advanced'],
        default='simple',
        help='Méthode de détection des intervenants (défaut: simple)'
    )
    parser.add_argument(
        '--num-speakers',
        type=int,
        default=None,
        help='Nombre d\'intervenants attendu (auto-détection si non spécifié)'
    )
    parser.add_argument(
        '--love-threshold',
        type=float,
        default=0.1,
        help='Seuil minimum pour l\'analyse d\'amour (défaut: 0.1)'
    )
    
    args = parser.parse_args()
    
    # Vérifier le fichier d'entrée
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Erreur : Le fichier {input_path} n'existe pas")
        sys.exit(1)
    
    # Créer le dossier de sortie
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🎙️  Transcription avec analyse d'amour : {input_path.name}")
    print(f"📂 Sortie dans : {output_dir}")
    print(f"🎯 Formats : {', '.join(args.formats)}")
    print("=" * 60)
    
    try:
        # 1. Transcription avec détection des intervenants
        print("🔤 Transcription avec Whisper...")
        transcriber = SimpleAudioTranscriberWithSpeakers()
        
        transcription_result = transcriber.transcribe_with_simple_speakers(
            str(input_path),
            word_timestamps=True
        )
        
        if not transcription_result:
            print("❌ Erreur : La transcription a échoué")
            sys.exit(1)
        
        print(f"✅ Transcription terminée :")
        print(f"   - Durée : {transcription_result['metadata']['duration']:.1f}s")
        print(f"   - Segments : {len(transcription_result['transcription']['segments'])}")
        if 'speaker_distribution' in transcription_result['metadata']:
            print(f"   - Intervenants détectés : {len(transcription_result['metadata']['speaker_distribution'])}")
        
        # 2. Analyse d'amour
        print("\n💕 Analyse des types d'amour...")
        start_time = time.time()
        
        love_analyzer = LoveTypeAnalyzer(min_score_threshold=args.love_threshold)
        enriched_result = love_analyzer.analyze_transcription(transcription_result)
        
        analysis_time = time.time() - start_time
        print(f"✅ Analyse d'amour terminée en {analysis_time:.1f}s")
        
        # Afficher les statistiques d'amour
        love_stats = enriched_result['love_analysis']['statistics_by_type']
        print(f"📊 Types d'amour détectés :")
        for love_type, stats in love_stats.items():
            if stats.get('total_intensity', 0) > 0:
                print(f"   - {love_type.capitalize()} : {stats['total_intensity']:.2f} "
                      f"({stats['segments_count']} segments, avg: {stats['average_score']:.3f})")
        
        # 3. Export enrichi
        print(f"\n📤 Export des résultats...")
        export_manager = EnrichedExportManager()
        
        # Nom de base pour les fichiers
        base_name = input_path.stem
        output_base = output_dir / f"{base_name}_love_analysis"
        
        final_result = export_manager.export_with_love_analysis(
            enriched_result,
            str(output_base),
            formats=args.formats
        )
        
        print(f"✅ Export terminé dans {output_dir}")
        
        # 4. Résumé final
        print("\n" + "=" * 60)
        print("📋 RÉSUMÉ DE L'ANALYSE")
        print("=" * 60)
        
        # Statistiques générales
        metadata = final_result['metadata']
        love_analysis = final_result['love_analysis']
        
        print(f"📁 Fichier : {metadata['file']}")
        print(f"⏱️  Durée : {metadata['duration']:.1f} secondes")
        print(f"🔤 Mots détectés : {metadata.get('word_count', 'N/A')}")
        
        if 'speaker_distribution' in metadata:
            print(f"👥 Intervenants :")
            for speaker, info in metadata['speaker_distribution'].items():
                print(f"   - {speaker} : {info['word_count']} mots ({info['percentage']:.1f}%)")
        
        print(f"\n💕 Analyse d'amour :")
        print(f"   - Segments analysés : {love_analysis['total_segments']}")
        print(f"   - Segments avec amour : {love_analysis['segments_with_love_content']}")
        print(f"   - Couverture : {love_analysis['love_coverage_percentage']}%")
        
        # Top 3 des types d'amour
        sorted_types = sorted(
            love_stats.items(), 
            key=lambda x: x[1].get('total_intensity', 0), 
            reverse=True
        )[:3]
        
        print(f"\n🏆 Top 3 des types d'amour :")
        for i, (love_type, stats) in enumerate(sorted_types, 1):
            if stats.get('total_intensity', 0) > 0:
                print(f"   {i}. {love_type.capitalize()} : {stats['total_intensity']:.2f} "
                      f"(Moyenne: {stats['average_score']:.3f})")
        
        print(f"\n🎨 Fichiers générés dans : {output_dir}")
        for format_type in args.formats:
            if format_type == 'json':
                print(f"   📋 JSON complet : {base_name}_love_analysis.json")
            elif format_type == 'csv':
                print(f"   📊 CSV enrichi : {base_name}_love_data.csv")
            elif format_type == 'artistic':
                print(f"   🎨 Format artistique : {base_name}_love_artistic.json")
            elif format_type == 'srt':
                print(f"   📺 Sous-titres : {base_name}_love_subtitles.srt")
            elif format_type == 'summary':
                print(f"   📄 Résumé : {base_name}_love_summary.txt")
        
        print("🎉 Transcription avec analyse d'amour terminée avec succès !")
        
    except KeyboardInterrupt:
        print("\n⚠️ Transcription interrompue par l'utilisateur")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Erreur pendant la transcription : {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()