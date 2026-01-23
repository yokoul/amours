#!/usr/bin/env python3
"""
Script de reconstruction de phrases à partir d'une transcription existante.
"""

import sys
import json
from pathlib import Path
import argparse

# Ajouter src au PATH
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from sentence_reconstructor import SentenceReconstructor


def main():
    """Reconstruit les phrases d'une transcription existante."""
    parser = argparse.ArgumentParser(
        description='Reconstruction de phrases à partir d\'une transcription JSON'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Fichier JSON de transcription à reconstruire'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Fichier JSON de sortie (optionnel)'
    )
    
    args = parser.parse_args()
    
    # Vérifier le fichier d'entrée
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"❌ Erreur : Le fichier {input_file} n'existe pas")
        sys.exit(1)
    
    # Déterminer le fichier de sortie
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = input_file.with_name(input_file.stem + "_sentences.json")
    
    print(f"🔧 Reconstruction de phrases : {input_file.name}")
    print(f"📂 Sortie : {output_file.name}")
    print("=" * 60)
    
    try:
        # 1. Charger les données
        print("📂 Chargement de la transcription...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_segments = data['transcription']['segments']
        print(f"✅ {len(original_segments)} segments chargés")
        
        # 2. Reconstruction
        print("🔧 Reconstruction des phrases complètes...")
        reconstructor = SentenceReconstructor()
        reconstructed_segments = reconstructor.reconstruct_sentences(original_segments)
        
        # 3. Statistiques
        stats = reconstructor.get_reconstruction_stats(original_segments, reconstructed_segments)
        print(f"\\n📊 RÉSULTATS DE LA RECONSTRUCTION :")
        print(f"   📉 {stats['original_segments']} segments → {stats['reconstructed_sentences']} phrases")
        print(f"   📊 Réduction : {stats['reduction_count']} unités (-{stats['reduction_percentage']}%)")
        print(f"   📝 Mots par unité : {stats['avg_words_original']:.1f} → {stats['avg_words_reconstructed']:.1f}")
        
        # 4. Mettre à jour les données
        data['transcription']['segments'] = reconstructed_segments
        data['metadata']['sentence_reconstruction'] = stats
        data['metadata']['reconstruction_enabled'] = True
        data['metadata']['segment_count'] = len(reconstructed_segments)
        
        # 5. Sauvegarder
        print(f"\\n💾 Sauvegarde dans {output_file.name}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Reconstruction terminée !")
        
        # 6. Exemples
        print(f"\\n🎯 EXEMPLES DE PHRASES RECONSTRUITES :")
        print("-" * 60)
        for i, segment in enumerate(reconstructed_segments[:3], 1):
            text = segment['text']
            speaker = segment.get('speaker', 'Inconnu')
            original_count = len(segment.get('original_segments', []))
            word_count = len(segment.get('words', []))
            
            print(f"{i}. [{speaker} - {segment['start']:.1f}s - {word_count} mots - {original_count} segments fusionnés]")
            print(f"   \"{text[:100]}{'...' if len(text) > 100 else ''}\"")
            print()
        
        print(f"💡 Pour analyser l'amour sur les phrases complètes :")
        print(f"   python analyze_love.py --input \"{output_file}\" --no-reconstruct")
        
    except Exception as e:
        print(f"❌ Erreur : {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()