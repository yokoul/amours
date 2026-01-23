#!/usr/bin/env python3
"""
Script de transcription avec phrases complètes intégrées.
Version optimisée qui reconstruit les phrases directement lors de la transcription.
"""

import sys
import time
from pathlib import Path
import argparse

# Ajouter src au PATH
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from simple_transcriber_with_speakers import SimpleAudioTranscriberWithSpeakers
from sentence_reconstructor import SentenceReconstructor
from export import ExportManager


def main():
    """Fonction principale de transcription avec phrases complètes."""
    parser = argparse.ArgumentParser(
        description='Transcription audio avec phrases complètes et détection d\'intervenants'
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
        default='output_sentences',
        help='Dossier de sortie (défaut: output_sentences)'
    )
    parser.add_argument(
        '--formats', '-f',
        nargs='+',
        choices=['json', 'csv', 'srt', 'words'],
        default=['json'],
        help='Formats d\'export à générer'
    )
    parser.add_argument(
        '--whisper-model',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        default='medium',
        help='Modèle Whisper à utiliser (défaut: medium)'
    )
    parser.add_argument(
        '--no-reconstruct',
        action='store_true',
        help='Désactiver la reconstruction de phrases'
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
    
    print(f"🎙️  Transcription avec phrases complètes : {input_path.name}")
    print(f"📂 Sortie dans : {output_dir}")
    print(f"🎯 Formats : {', '.join(args.formats)}")
    print(f"🤖 Modèle Whisper : {args.whisper_model}")
    print(f"🔧 Reconstruction : {'❌' if args.no_reconstruct else '✅'}")
    print("=" * 60)
    
    try:
        # 1. Transcription initiale avec Whisper
        print("🔤 Transcription initiale...")
        transcriber = SimpleAudioTranscriberWithSpeakers(
            model_name=args.whisper_model,
            language='fr'
        )
        
        transcription_result = transcriber.transcribe_with_simple_speakers(
            str(input_path),
            word_timestamps=True
        )
        
        if not transcription_result:
            print("❌ Erreur : La transcription a échoué")
            sys.exit(1)
        
        # 2. Reconstruction des phrases si activée
        if not args.no_reconstruct:
            print("🔧 Reconstruction des phrases complètes...")
            start_time = time.time()
            
            reconstructor = SentenceReconstructor()
            original_segments = transcription_result['transcription']['segments']
            reconstructed_segments = reconstructor.reconstruct_sentences(original_segments)
            
            reconstruction_time = time.time() - start_time
            
            # Calculer les statistiques
            stats = reconstructor.get_reconstruction_stats(original_segments, reconstructed_segments)
            print(f"   📊 {stats['original_segments']} segments → {stats['reconstructed_sentences']} phrases")
            print(f"   📉 Réduction: {stats['reduction_count']} segments (-{stats['reduction_percentage']}%)")
            print(f"   📝 Mots moyens par unité: {stats['avg_words_original']:.1f} → {stats['avg_words_reconstructed']:.1f}")
            print(f"   ⏱️ Reconstruction en: {reconstruction_time:.1f}s")
            
            # Remplacer les segments par les phrases reconstruites
            transcription_result['transcription']['segments'] = reconstructed_segments
            transcription_result['metadata']['sentence_reconstruction'] = stats
            transcription_result['metadata']['reconstruction_enabled'] = True
        else:
            transcription_result['metadata']['reconstruction_enabled'] = False
        
        # 3. Mise à jour des statistiques après reconstruction
        segments = transcription_result['transcription']['segments']
        total_words = sum(len(seg.get('words', [])) for seg in segments)
        transcription_result['metadata']['word_count'] = total_words
        transcription_result['metadata']['segment_count'] = len(segments)
        
        # 4. Re-détection des intervenants sur les phrases complètes
        if not args.no_reconstruct:
            print("👥 Attribution des intervenants aux phrases...")
            # Les intervenants sont déjà assignés par segment, on les conserve
            # lors de la reconstruction dans le SentenceReconstructor
        
        # 5. Afficher les statistiques finales
        metadata = transcription_result['metadata']
        
        print(f"\\n📊 STATISTIQUES FINALES")
        print("=" * 60)
        print(f"📁 Fichier : {metadata['file']}")
        print(f"⏱️  Durée : {metadata['duration']:.1f} secondes")
        print(f"🔢 Unités de texte : {len(segments)} {'phrases' if not args.no_reconstruct else 'segments'}")
        print(f"💬 Mots détectés : {metadata.get('word_count', 'N/A')}")
        
        if 'speaker_distribution' in metadata:
            print(f"\\n👥 INTERVENANTS DÉTECTÉS :")
            for speaker, info in metadata['speaker_distribution'].items():
                print(f"   🔹 {speaker:<12} : {info['word_count']:>4} mots ({info['percentage']:>5.1f}%)")
        
        # 6. Export des résultats
        print(f"\\n📤 Export des transcriptions...")
        export_manager = ExportManager()
        
        # Nom de base pour les fichiers
        base_name = input_path.stem
        suffix = "_sentences" if not args.no_reconstruct else "_segments"
        
        exports_generated = []
        
        if 'json' in args.formats:
            json_path = output_dir / f"{base_name}{suffix}_complete.json"
            export_manager.export_json(transcription_result, str(json_path))
            exports_generated.append(f"📋 JSON complet : {json_path.name}")
        
        if 'csv' in args.formats:
            csv_path = output_dir / f"{base_name}{suffix}_data.csv"
            export_manager.export_csv(transcription_result, str(csv_path))
            exports_generated.append(f"📊 CSV données : {csv_path.name}")
        
        if 'srt' in args.formats:
            srt_path = output_dir / f"{base_name}{suffix}_subtitles.srt"
            export_manager.export_srt_subtitles(transcription_result, str(srt_path))
            exports_generated.append(f"📺 Sous-titres : {srt_path.name}")
        
        if 'words' in args.formats:
            words_path = output_dir / f"{base_name}_words.json"
            export_manager.export_words_only(transcription_result, str(words_path))
            exports_generated.append(f"🔤 Mots seuls : {words_path.name}")
        
        print(f"✅ Export terminé dans {output_dir}")
        
        # 7. Résumé des fichiers générés
        print(f"\\n🎨 FICHIERS GÉNÉRÉS :")
        for export_info in exports_generated:
            print(f"   {export_info}")
        
        # 8. Exemple de contenu
        print(f"\\n🎯 APERÇU DE LA TRANSCRIPTION :")
        print("-" * 60)
        unit_name = "phrases" if not args.no_reconstruct else "segments"
        
        for i, segment in enumerate(segments[:3], 1):  # 3 premières unités
            text = segment['text'].strip()
            speaker = segment.get('speaker', 'Inconnu')
            start_time = segment['start']
            word_count = len(segment.get('words', []))
            
            print(f"{i}. [{speaker} - {start_time:.1f}s - {word_count} mots]")
            print(f"   \"{text[:120]}{'...' if len(text) > 120 else ''}\"")
            print()
        
        if len(segments) > 3:
            print(f"   ... et {len(segments) - 3} autres {unit_name}")
        
        # 9. Conseil pour l'analyse d'amour
        json_file = f"{base_name}{suffix}_complete.json"
        print(f"\\n💡 POUR L'ANALYSE D'AMOUR :")
        print(f"   python analyze_love.py --input \"{output_dir}/{json_file}\"")
        
        if not args.no_reconstruct:
            print(f"\\n✨ Avantages des phrases complètes :")
            print(f"   • Analyse sémantique plus précise")
            print(f"   • Contexte linguistique préservé")  
            print(f"   • Réduction de {stats['reduction_percentage']}% des unités à traiter")
        
        print("\\n🎉 Transcription terminée avec succès !")
        
    except KeyboardInterrupt:
        print("\\n⚠️ Transcription interrompue par l'utilisateur")
        sys.exit(1)
        
    except Exception as e:
        print(f"\\n❌ Erreur pendant la transcription : {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()