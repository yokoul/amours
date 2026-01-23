"""
Exemple d'utilisation du système de transcription audio.
Démontre les différentes fonctionnalités et formats d'export.
"""

import sys
from pathlib import Path

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcriber import AudioTranscriber
from audio_processor import AudioProcessor
from export import ExportManager


def example_basic_transcription():
    """Exemple de transcription basique."""
    print("=== Transcription basique ===")
    
    # Chemin vers votre fichier audio (à adapter)
    audio_file = "../audio/sample.mp3"  # Remplacez par votre fichier
    
    if not Path(audio_file).exists():
        print(f"⚠️  Fichier audio non trouvé : {audio_file}")
        print("Placez un fichier audio dans le dossier 'audio/' pour tester")
        return
    
    try:
        # Initialiser le transcripteur
        transcriber = AudioTranscriber(model_name="tiny", language="fr")
        
        # Transcrire avec timecodes
        result = transcriber.transcribe_with_timestamps(audio_file)
        
        # Afficher quelques informations
        print(f"📁 Fichier : {result['metadata']['file']}")
        print(f"⏱️  Durée : {result['metadata']['duration']:.2f}s")
        print(f"📝 Texte : {result['transcription']['text']}")
        print(f"🎯 Segments : {len(result['transcription']['segments'])}")
        
        # Compter les mots
        word_count = sum(len(seg['words']) for seg in result['transcription']['segments'])
        print(f"🔤 Mots : {word_count}")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return None


def example_audio_processing():
    """Exemple de prétraitement audio."""
    print("\n=== Prétraitement audio ===")
    
    audio_file = "../audio/sample.mp3"
    
    if not Path(audio_file).exists():
        print("⚠️  Fichier audio non trouvé pour le prétraitement")
        return
    
    try:
        processor = AudioProcessor()
        
        # Analyser les caractéristiques
        features = processor.get_audio_features(audio_file)
        print("📊 Caractéristiques audio :")
        for key, value in features.items():
            print(f"   {key}: {value}")
        
        # Convertir en WAV si nécessaire
        if not audio_file.endswith('.wav'):
            wav_file = processor.convert_to_wav(audio_file, "../audio/converted.wav")
            print(f"🔄 Converti en : {wav_file}")
        
        # Normaliser l'audio
        normalized_file = processor.normalize_audio(audio_file, "../audio/normalized.wav")
        print(f"🎚️  Normalisé : {normalized_file}")
        
    except Exception as e:
        print(f"❌ Erreur de traitement : {e}")


def example_export_formats(transcription_result):
    """Exemple des différents formats d'export."""
    if not transcription_result:
        print("⚠️  Pas de données de transcription à exporter")
        return
    
    print("\n=== Formats d'export ===")
    
    export_manager = ExportManager()
    
    try:
        # Export JSON complet
        export_manager.export_json(transcription_result, "../output/transcription.json")
        
        # Export CSV
        export_manager.export_csv(transcription_result, "../output/transcription.csv")
        
        # Export mots uniquement
        export_manager.export_words_only(transcription_result, "../output/words_only.json")
        
        # Export format artistique
        export_manager.export_artistic_format(transcription_result, "../output/artistic_format.json")
        
        # Export sous-titres SRT
        export_manager.export_srt_subtitles(transcription_result, "../output/subtitles.srt")
        
        print("✅ Tous les formats exportés dans le dossier 'output/'")
        
    except Exception as e:
        print(f"❌ Erreur d'export : {e}")


def example_segment_analysis(transcription_result):
    """Exemple d'analyse des segments et mots."""
    if not transcription_result:
        return
    
    print("\n=== Analyse détaillée ===")
    
    segments = transcription_result['transcription']['segments']
    
    for i, segment in enumerate(segments[:3]):  # Afficher les 3 premiers segments
        print(f"\n🎬 Segment {i+1} ({segment['start']:.2f}s - {segment['end']:.2f}s):")
        print(f"   Texte : '{segment['text']}'")
        print(f"   Durée : {segment['duration']:.2f}s")
        print(f"   Mots ({len(segment['words'])}) :")
        
        for word in segment['words'][:5]:  # Afficher les 5 premiers mots
            print(f"      '{word['word']}' ({word['start']:.2f}s - {word['end']:.2f}s)")
        
        if len(segment['words']) > 5:
            print(f"      ... et {len(segment['words']) - 5} autres mots")


def create_sample_audio():
    """Crée un fichier audio de test avec synthèse vocale (optionnel)."""
    print("\n=== Création d'un échantillon audio ===")
    print("💡 Pour tester, ajoutez un fichier audio dans le dossier 'audio/'")
    print("   Formats supportés : MP3, WAV, M4A, FLAC")
    print("   Exemple : audio/discussion.mp3")


def main():
    """Fonction principale des exemples."""
    print("🎵 Exemples de Transcription Audio avec Timecodes")
    print("=" * 50)
    
    # Créer les dossiers nécessaires
    Path("../audio").mkdir(exist_ok=True)
    Path("../output").mkdir(exist_ok=True)
    
    # Exemples
    create_sample_audio()
    example_audio_processing()
    
    # Transcription principale
    result = example_basic_transcription()
    
    if result:
        example_segment_analysis(result)
        example_export_formats(result)
    
    print("\n✨ Exemples terminés !")
    print("💡 Consultez les fichiers dans le dossier 'output/' pour voir les résultats")


if __name__ == "__main__":
    main()