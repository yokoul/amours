#!/usr/bin/env python3
"""
Script de transcription audio avec détection d'intervenants.
Génère uniquement les fichiers de transcription.
"""

import sys
import time
import json
from pathlib import Path
import argparse

# Ajouter src au PATH
current_dir = Path(__file__).parent
src_dir = current_dir / 'src'
sys.path.insert(0, str(src_dir))

from src.simple_transcriber_with_speakers import SimpleAudioTranscriberWithSpeakers
from src.export import ExportManager


def main():
    """Fonction principale de transcription."""
    parser = argparse.ArgumentParser(
        description='Transcription audio avec détection des intervenants'
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
        default='output_transcription',
        help='Dossier de sortie (défaut: output_transcription)'
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
        '--reconstruct-sentences',
        action='store_true',
        help='Reconstruire les phrases complètes automatiquement'
    )
    parser.add_argument(
        '--with-semantic-analysis',
        action='store_true',
        help='Inclure automatiquement l\'analyse sémantique des types d\'amour'
    )
    
    args = parser.parse_args()
    
    # Vérifier le fichier d'entrée
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Erreur : Le fichier {input_path} n'existe pas")
        sys.exit(1)
    
    # Vérifier que c'est un fichier audio
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma'}
    if input_path.suffix.lower() not in audio_extensions:
        print(f"⚠️  Attention : Extension non reconnue. Formats supportés : {', '.join(audio_extensions)}")
    
    # Créer le dossier de sortie
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🎙️  Transcription audio : {input_path.name}")
    print(f"📂 Sortie dans : {output_dir}")
    print(f"🎯 Formats : {', '.join(args.formats)}")
    print(f"🤖 Modèle Whisper : {args.whisper_model}")
    print("=" * 60)
    
    try:
        # 1. Initialiser le transcripteur
        print("🔧 Initialisation du transcripteur...")
        transcriber = SimpleAudioTranscriberWithSpeakers(
            model_name=args.whisper_model,
            language='fr',
            reconstruct_sentences=args.reconstruct_sentences
        )
        
        # 2. Transcription avec détection des intervenants
        print("🎵 Transcription en cours...")
        start_time = time.time()
        
        transcription_result = transcriber.transcribe_with_simple_speakers(
            str(input_path),
            word_timestamps=True
        )
        
        if not transcription_result:
            print("❌ Erreur : La transcription a échoué")
            sys.exit(1)
        
        transcription_time = time.time() - start_time
        print(f"✅ Transcription terminée en {transcription_time:.1f}s")
        
        # 3. Afficher les statistiques
        metadata = transcription_result['metadata']
        segments = transcription_result['transcription']['segments']
        
        print(f"\n📊 STATISTIQUES DE TRANSCRIPTION")
        print("=" * 60)
        print(f"📁 Fichier : {metadata['file']}")
        print(f"⏱️  Durée : {metadata['duration']:.1f} secondes")
        print(f"🔢 Segments : {len(segments)}")
        
        if 'word_count' in metadata:
            print(f"💬 Mots détectés : {metadata['word_count']}")
        
        if 'speaker_distribution' in metadata:
            print(f"\n👥 INTERVENANTS DÉTECTÉS :")
            for speaker, info in metadata['speaker_distribution'].items():
                print(f"   🔹 {speaker:<12} : {info['word_count']:>4} mots ({info['percentage']:>5.1f}%)")
        
        # 4. Export des résultats
        print(f"\n📤 Export des transcriptions...")
        export_manager = ExportManager()
        
        # Nom de base pour les fichiers
        base_name = input_path.stem
        
        exports_generated = []
        
        if 'json' in args.formats:
            json_path = output_dir / f"{base_name}_with_speakers_complete.json"
            export_manager.export_json(transcription_result, str(json_path))
            exports_generated.append(f"📋 JSON complet : {json_path.name}")
        
        if 'csv' in args.formats:
            csv_path = output_dir / f"{base_name}_with_speakers_data.csv"
            export_manager.export_csv(transcription_result, str(csv_path))
            exports_generated.append(f"📊 CSV données : {csv_path.name}")
        
        if 'srt' in args.formats:
            srt_path = output_dir / f"{base_name}_with_speakers_subtitles.srt"
            export_manager.export_srt_subtitles(transcription_result, str(srt_path))
            exports_generated.append(f"📺 Sous-titres : {srt_path.name}")
        
        if 'words' in args.formats:
            words_path = output_dir / f"{base_name}_words.json"
            export_manager.export_words_only(transcription_result, str(words_path))
            exports_generated.append(f"🔤 Mots seuls : {words_path.name}")
        
        print(f"✅ Export terminé dans {output_dir}")
        
        # 4b. Analyse sémantique si demandée
        if args.with_semantic_analysis and 'json' in args.formats:
            print(f"\n🧠 ANALYSE SÉMANTIQUE EN COURS...")
            print("=" * 60)
            
            try:
                # Import de l'analyseur
                sys.path.insert(0, str(src_dir))
                from love_analyzer import LoveAnalyzer
                
                # Analyser le fichier JSON généré
                json_path = output_dir / f"{base_name}_with_speakers_complete.json"
                analyzer = LoveAnalyzer()
                
                # Charger et analyser
                with open(json_path, 'r', encoding='utf-8') as f:
                    transcription_data = json.load(f)
                
                semantic_results = analyzer.analyze_transcription(
                    transcription_data,
                    threshold=0.15
                )
                
                # Ajouter l'analyse au JSON existant
                transcription_data['semantic_analysis'] = semantic_results
                
                # Sauvegarder le fichier enrichi
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(transcription_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Analyse sémantique ajoutée au fichier JSON")
                
                # Afficher un résumé
                if 'summary' in semantic_results:
                    summary = semantic_results['summary']
                    print(f"\n📊 RÉSUMÉ DE L'ANALYSE :")
                    print(f"   💗 Types d'amour détectés : {len(summary['detected_types'])}")
                    
                    if summary['top_types']:
                        print(f"   🏆 Type dominant : {summary['top_types'][0]['type']} ({summary['top_types'][0]['score']:.2f})")
                        
                        print(f"\n🎆 TOP 3 DES TYPES D'AMOUR :")
                        for i, love_type in enumerate(summary['top_types'][:3], 1):
                            print(f"   {i}. {love_type['type'].title()} : {love_type['score']:.2f}")
                
            except Exception as e:
                print(f"⚠️ Erreur lors de l'analyse sémantique : {str(e)}")
                print("   La transcription est disponible sans analyse sémantique")
        
        # 5. Résumé des fichiers générés
        print(f"\n🎨 FICHIERS GÉNÉRÉS :")
        for export_info in exports_generated:
            print(f"   {export_info}")
        
        # 6. Exemple de contenu transcrit
        print(f"\n🎯 APERÇU DE LA TRANSCRIPTION :")
        print("-" * 40)
        for i, segment in enumerate(segments[:3], 1):  # 3 premiers segments
            text = segment['text'].strip()
            speaker = segment.get('speaker', 'Inconnu')
            start_time = segment['start']
            
            print(f"{i}. [{speaker} - {start_time:.1f}s] \"{text[:80]}{'...' if len(text) > 80 else ''}\"")
        
        if len(segments) > 3:
            print(f"   ... et {len(segments) - 3} autres segments")
        
        print(f"\n💡 CONSEIL :")
        print(f"   Pour analyser les types d'amour, utilisez :")
        print(f"   python analyze_love.py --input \"{output_dir}/{base_name}_with_speakers_complete.json\"")
        
        print("\n🎉 Transcription terminée avec succès !")
        
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