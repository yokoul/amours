#!/usr/bin/env python3
"""
Script d'analyse d'amour sur des transcriptions existantes.
Utilise sentence-transformers pour l'analyse sémantique.
"""

import sys
import json
import time
from pathlib import Path
import argparse

# Ajouter src au PATH
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from love_analyzer import LoveTypeAnalyzer
from enriched_export import EnrichedExportManager


def main():
    """Analyser les types d'amour dans une transcription existante."""
    parser = argparse.ArgumentParser(
        description='Analyse des types d\'amour sur transcription existante'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Fichier JSON de transcription à analyser'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='output_love',
        help='Dossier de sortie pour l\'analyse d\'amour'
    )
    parser.add_argument(
        '--formats', '-f',
        nargs='+',
        choices=['json', 'csv', 'artistic', 'srt', 'summary'],
        default=['json', 'summary'],
        help='Formats d\'export à générer'
    )
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=0.1,
        help='Seuil minimum pour détection d\'amour (défaut: 0.1)'
    )
    parser.add_argument(
        '--semantic',
        action='store_true',
        default=True,
        help='Utiliser l\'analyse sémantique (sentence-transformers)'
    )
    parser.add_argument(
        '--no-semantic',
        dest='semantic',
        action='store_false',
        help='Désactiver l\'analyse sémantique'
    )
    parser.add_argument(
        '--reconstruct',
        action='store_true',
        default=True,
        help='Reconstruire les phrases complètes (défaut: activé)'
    )
    parser.add_argument(
        '--no-reconstruct',
        dest='reconstruct',
        action='store_false',
        help='Désactiver la reconstruction de phrases'
    )
    
    args = parser.parse_args()
    
    # Vérifier le fichier d'entrée
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"❌ Erreur : Le fichier {input_file} n'existe pas")
        sys.exit(1)
    
    if not input_file.suffix.lower() == '.json':
        print(f"❌ Erreur : Le fichier doit être un JSON de transcription")
        sys.exit(1)
    
    # Créer le dossier de sortie
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"💕 Analyse d'amour : {input_file.name}")
    print(f"📂 Sortie dans : {output_dir}")
    print(f"🎯 Formats : {', '.join(args.formats)}")
    print(f"🔍 Seuil : {args.threshold}")
    print(f"🤖 Analyse sémantique : {'✅' if args.semantic else '❌'}")
    print(f"🔧 Reconstruction phrases : {'✅' if args.reconstruct else '❌'}")
    print("=" * 60)
    
    try:
        # 1. Charger les données de transcription
        print("📂 Chargement de la transcription...")
        with open(input_file, 'r', encoding='utf-8') as f:
            transcription_data = json.load(f)
        
        segments_count = len(transcription_data.get('transcription', {}).get('segments', []))
        print(f"✅ Transcription chargée : {segments_count} segments")
        
        # 2. Initialiser l'analyseur d'amour
        print("🤖 Initialisation de l'analyseur...")
        start_init = time.time()
        
        analyzer = LoveTypeAnalyzer(
            min_score_threshold=args.threshold,
            use_semantic_analysis=args.semantic,
            reconstruct_sentences=args.reconstruct
        )
        
        init_time = time.time() - start_init
        print(f"✅ Analyseur initialisé en {init_time:.1f}s")
        
        # 3. Analyser les types d'amour
        print("💝 Analyse des types d'amour...")
        start_analysis = time.time()
        
        enriched_data = analyzer.analyze_transcription(transcription_data)
        
        analysis_time = time.time() - start_analysis
        print(f"✅ Analyse terminée en {analysis_time:.1f}s")
        
        # 4. Afficher les statistiques
        love_analysis = enriched_data['love_analysis']
        love_stats = love_analysis['statistics_by_type']
        
        print(f"\n📊 RÉSULTATS DE L'ANALYSE")
        print("=" * 60)
        print(f"📁 Fichier source : {transcription_data['metadata']['file']}")
        print(f"⏱️ Durée audio : {transcription_data['metadata']['duration']:.1f}s")
        print(f"🔢 Segments totaux : {love_analysis['total_segments']}")
        print(f"💕 Segments avec amour : {love_analysis['segments_with_love_content']}")
        print(f"📈 Couverture : {love_analysis['love_coverage_percentage']}%")
        
        # Top types d'amour détectés
        print(f"\n💖 TYPES D'AMOUR DÉTECTÉS :")
        sorted_types = sorted(
            love_stats.items(),
            key=lambda x: x[1].get('total_intensity', 0),
            reverse=True
        )
        
        found_love = False
        for love_type, stats in sorted_types:
            intensity = stats.get('total_intensity', 0)
            if intensity > 0:
                found_love = True
                print(f"   🔹 {love_type.capitalize():<15} : {intensity:>6.2f} "
                      f"(avg: {stats['average_score']:.3f}, "
                      f"{stats['segments_count']} segments)")
        
        if not found_love:
            print("   ℹ️  Aucun type d'amour significatif détecté")
        
        # 5. Export des résultats
        print(f"\n📤 Export des résultats...")
        export_manager = EnrichedExportManager()
        
        # Nom de base pour les fichiers
        base_name = input_file.stem
        if base_name.endswith('_complete'):
            base_name = base_name.replace('_complete', '')
        elif base_name.endswith('_with_speakers'):
            base_name = base_name.replace('_with_speakers', '')
        
        output_base = output_dir / f"{base_name}_love_analysis"
        
        final_result = export_manager.export_with_love_analysis(
            enriched_data,
            str(output_base),
            formats=args.formats
        )
        
        print(f"✅ Export terminé dans {output_dir}")
        
        # 6. Résumé des fichiers générés
        print(f"\n🎨 FICHIERS GÉNÉRÉS :")
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
        
        # 7. Quelques exemples de segments analysés
        if found_love:
            print(f"\n🎯 EXEMPLES D'ANALYSE :")
            segments_with_love = []
            for segment in enriched_data['transcription']['segments']:
                if segment.get('love_confidence', 0) > args.threshold:
                    segments_with_love.append(segment)
            
            # Prendre les 3 meilleurs segments
            top_segments = sorted(
                segments_with_love,
                key=lambda x: x.get('love_confidence', 0),
                reverse=True
            )[:3]
            
            for i, segment in enumerate(top_segments, 1):
                love_type = segment.get('dominant_love_type', 'inconnu')
                confidence = segment.get('love_confidence', 0)
                text = segment['text'][:100] + "..." if len(segment['text']) > 100 else segment['text']
                
                print(f"{i}. {love_type.capitalize()} ({confidence:.3f}) :")
                print(f"   \"{text}\"")
                if 'speaker' in segment:
                    print(f"   [{segment['speaker']} - {segment['start']:.1f}s]")
                print()
        
        print("🎉 Analyse d'amour terminée avec succès !")
        
    except KeyboardInterrupt:
        print("\n⚠️ Analyse interrompue par l'utilisateur")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Erreur pendant l'analyse : {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()