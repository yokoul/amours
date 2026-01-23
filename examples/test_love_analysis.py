#!/usr/bin/env python3
"""
Test de l'analyse d'amour sur un fichier audio existant.
"""

import sys
import os
from pathlib import Path

# Ajouter src au PATH
current_dir = Path(__file__).parent.parent  # Remonter au répertoire racine
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from love_analyzer import LoveTypeAnalyzer


def test_love_analysis_on_existing_data():
    """Test l'analyse d'amour sur des données JSON existantes."""
    # Chercher des fichiers JSON existants
    output_dirs = [
        Path("output"),
        Path("output_v1"),
        Path("output_v2")
    ]
    
    json_files = []
    for output_dir in output_dirs:
        if output_dir.exists():
            json_files.extend(output_dir.glob("*_complete.json"))
    
    if not json_files:
        print("❌ Aucun fichier de transcription trouvé")
        return
    
    # Prendre le premier fichier disponible
    test_file = json_files[0]
    print(f"🧪 Test d'analyse d'amour sur : {test_file}")
    print("=" * 60)
    
    try:
        import json
        
        # Charger les données
        with open(test_file, 'r', encoding='utf-8') as f:
            transcription_data = json.load(f)
        
        print(f"✅ Données chargées : {len(transcription_data['transcription']['segments'])} segments")
        
        # Analyser
        print("💕 Lancement de l'analyse d'amour...")
        
        analyzer = LoveTypeAnalyzer(min_score_threshold=0.05)
        enriched_data = analyzer.analyze_transcription(transcription_data)
        
        print("✅ Analyse terminée !")
        print("=" * 60)
        
        # Afficher les résultats
        love_analysis = enriched_data['love_analysis']
        
        print("📊 STATISTIQUES D'AMOUR")
        print("=" * 60)
        print(f"Score total d'amour : {love_analysis['total_love_score']:.3f}")
        print(f"Type dominant : {love_analysis['dominant_love_type']}")
        print(f"Segments analysés : {love_analysis['segments_analyzed']}")
        print(f"Segments avec amour détecté : {love_analysis['segments_with_love']}")
        
        print(f"\n💕 DÉTAIL PAR TYPE D'AMOUR")
        print("-" * 60)
        stats = love_analysis['statistics_by_type']
        
        # Trier par score total
        sorted_types = sorted(stats.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        for love_type, type_stats in sorted_types:
            if type_stats['total_score'] > 0:
                print(f"🔹 {love_type.upper()} :")
                print(f"   Score total : {type_stats['total_score']:.3f}")
                print(f"   Segments : {type_stats['segment_count']}")
                print(f"   Score moyen : {type_stats['average_score']:.3f}")
                print(f"   Score max : {type_stats['max_score']:.3f}")
                
                # Segments représentatifs
                if type_stats['representative_segments']:
                    print(f"   Segments représentatifs :")
                    for i, segment in enumerate(type_stats['representative_segments'][:2], 1):
                        text_preview = segment['text'][:50] + "..." if len(segment['text']) > 50 else segment['text']
                        print(f"     {i}. Score {segment['score']:.3f} : \"{text_preview}\"")
                        print(f"        Temps: {segment['start']:.1f}s-{segment['end']:.1f}s")
                print()
        
        # Quelques segments avec leurs analyses
        print("🎯 EXEMPLES D'ANALYSE")
        print("-" * 60)
        
        segments_with_love = []
        for segment in enriched_data['transcription']['segments']:
            if segment.get('love_confidence', 0) > 0.1:
                segments_with_love.append(segment)
        
        # Top 5 des segments avec le plus d'amour
        top_segments = sorted(segments_with_love, key=lambda x: x.get('love_confidence', 0), reverse=True)[:5]
        
        for i, segment in enumerate(top_segments, 1):
            print(f"{i}. Type dominant: {segment.get('dominant_love_type', 'inconnu')}")
            print(f"   Confiance: {segment.get('love_confidence', 0):.3f}")
            print(f"   Texte: \"{segment['text']}\"")
            print(f"   Scores: {segment['love_analysis']}")
            print(f"   Temps: {segment['start']:.1f}s - {segment['end']:.1f}s")
            if 'speaker' in segment:
                print(f"   Intervenant: {segment['speaker']}")
            print()
        
        # Test d'export du résumé
        print("📄 RÉSUMÉ TEXTUEL")
        print("=" * 60)
        summary = analyzer.get_love_summary(enriched_data)
        print(summary[:800] + "..." if len(summary) > 800 else summary)
        
        print("\n🎉 Test d'analyse d'amour réussi !")
        
    except Exception as e:
        print(f"❌ Erreur pendant le test : {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_love_analysis_on_existing_data()