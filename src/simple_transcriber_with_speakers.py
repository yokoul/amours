"""
Gestionnaire de transcription avec détection d'intervenants simplifiée.
Version stable qui utilise une approche hybride.
"""

import whisper
import librosa
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import warnings
try:
    from .sentence_reconstructor import SentenceReconstructor
except ImportError:
    from sentence_reconstructor import SentenceReconstructor
warnings.filterwarnings("ignore", category=UserWarning)

try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics.pairwise import cosine_similarity
    CLUSTERING_AVAILABLE = True
except ImportError:
    CLUSTERING_AVAILABLE = False

try:
    import pyannote.audio
    from pyannote.audio import Audio
    from pyannote.audio.pipelines.utils import get_devices
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False


class SimpleAudioTranscriberWithSpeakers:
    """Transcripteur audio avec détection d'intervenants simplifiée."""
    
    def __init__(
        self, 
        model_name: str = "medium", 
        language: str = "fr", 
        enable_speaker_detection: bool = True,
        reconstruct_sentences: bool = False
    ):
        """
        Initialise le transcripteur.
        
        Args:
            model_name: Modèle Whisper à utiliser
            language: Langue de l'audio
            enable_speaker_detection: Activer la détection d'intervenants
            reconstruct_sentences: Activer la reconstruction de phrases complètes
        """
        self.model_name = model_name
        self.language = language
        self.enable_speaker_detection = enable_speaker_detection
        self.reconstruct_sentences = reconstruct_sentences
        self.sentence_reconstructor = None
        self.model = None
        
        self._load_model()
        
        # Initialiser le reconstructeur de phrases si activé
        if self.reconstruct_sentences:
            self.sentence_reconstructor = SentenceReconstructor()
            print("✅ Reconstructeur de phrases initialisé")
    
    def _load_model(self):
        """Charge le modèle Whisper."""
        print(f"📥 Chargement du modèle Whisper '{self.model_name}'...")
        try:
            # Utiliser CPU pour éviter les problèmes de compatibilité
            self.model = whisper.load_model(self.model_name, device="cpu")
            print("✅ Modèle chargé avec succès !")
        except Exception as e:
            raise RuntimeError(f"Impossible de charger le modèle Whisper : {str(e)}")
    
    def _detect_speakers_simple(self, audio_path: str, segments: List[Dict]) -> Dict[str, Any]:
        """
        Détection d'intervenants simplifiée basée sur les caractéristiques audio.
        """
        if not self.enable_speaker_detection:
            return {"speakers": {}, "speaker_segments": []}
        
        print("👥 Détection des intervenants (méthode simplifiée)...")
        
        try:
            # Charger l'audio
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Extraire les caractéristiques pour chaque segment
            segment_features = []
            valid_segments = []
            
            for segment in segments:
                start_sample = int(segment["start"] * sr)
                end_sample = int(segment["end"] * sr)
                
                if start_sample < len(y) and end_sample <= len(y) and end_sample > start_sample:
                    segment_audio = y[start_sample:end_sample]
                    
                    if len(segment_audio) > 0:
                        # Extraire MFCC (caractéristiques spectrales)
                        mfccs = librosa.feature.mfcc(
                            y=segment_audio, 
                            sr=sr, 
                            n_mfcc=13
                        )
                        feature_vector = np.mean(mfccs, axis=1)
                        
                        segment_features.append(feature_vector)
                        valid_segments.append(segment)
            
            if len(segment_features) < 2:
                return {"speakers": {"Intervenant_1": {"total_time": sum(s["duration"] for s in segments)}}, "speaker_segments": []}
            
            # Clustering des caractéristiques
            if CLUSTERING_AVAILABLE:
                features_array = np.array(segment_features)
                
                # Déterminer le nombre optimal de clusters (2-4 intervenants)
                n_speakers = min(4, max(2, len(valid_segments) // 3))
                
                clustering = AgglomerativeClustering(
                    n_clusters=n_speakers,
                    linkage='ward'
                )
                speaker_labels = clustering.fit_predict(features_array)
            else:
                # Fallback : simple division basée sur l'énergie
                energies = [np.mean(librosa.feature.rms(y=y[int(s["start"]*sr):int(s["end"]*sr)])) for s in valid_segments]
                median_energy = np.median(energies)
                speaker_labels = [0 if e < median_energy else 1 for e in energies]
            
            # Créer les informations d'intervenants
            speakers = {}
            speaker_segments = []
            
            for i, (segment, speaker_id) in enumerate(zip(valid_segments, speaker_labels)):
                speaker_name = f"Intervenant_{speaker_id + 1}"
                
                if speaker_name not in speakers:
                    speakers[speaker_name] = {
                        "id": speaker_name,
                        "total_time": 0.0,
                        "segments_count": 0
                    }
                
                speakers[speaker_name]["total_time"] += segment["duration"]
                speakers[speaker_name]["segments_count"] += 1
                
                speaker_segments.append({
                    "segment_id": segment["id"],
                    "speaker": speaker_name,
                    "start": segment["start"],
                    "end": segment["end"],
                    "duration": segment["duration"]
                })
            
            print(f"✅ {len(speakers)} intervenants détectés (méthode acoustique)")
            
            return {
                "speakers": speakers,
                "speaker_segments": speaker_segments
            }
            
        except Exception as e:
            print(f"⚠️  Erreur détection d'intervenants : {e}")
            # Fallback : un seul intervenant
            return {
                "speakers": {"Intervenant_1": {"total_time": sum(s["duration"] for s in segments)}},
                "speaker_segments": []
            }
    
    def transcribe_with_simple_speakers(
        self, 
        audio_path: str, 
        word_timestamps: bool = True
    ) -> Dict[str, Any]:
        """
        Transcrit avec détection d'intervenants simplifiée et reconstruction de phrases.
        """
        if self.model is None:
            self._load_model()
        
        audio_file = Path(audio_path)
        print(f"🎵 Analyse de : {audio_file.name}")
        
        # Transcription Whisper standard
        print("🎯 Transcription en cours...")
        
        options = {
            "language": self.language,
            "word_timestamps": word_timestamps,
            "verbose": False
        }
        
        result = self.model.transcribe(str(audio_path), **options)
        
        # Préparer les segments initiaux
        initial_segments = []
        for segment in result["segments"]:
            segment_data = {
                "id": segment["id"],
                "start": round(segment["start"], 3),
                "end": round(segment["end"], 3),
                "duration": round(segment["end"] - segment["start"], 3),
                "text": segment["text"].strip(),
                "words": []
            }
            
            if word_timestamps and "words" in segment:
                for word_info in segment["words"]:
                    start_time = round(word_info["start"], 3)
                    end_time = round(word_info["end"], 3)
                    segment_data["words"].append({
                        "word": word_info["word"],
                        "start": start_time,
                        "end": end_time,
                        "duration": round(end_time - start_time, 3),
                        "confidence": word_info.get("probability", 0.0)
                    })
            
            initial_segments.append(segment_data)
        
        # Reconstruction des phrases si activée
        if self.reconstruct_sentences and self.sentence_reconstructor:
            print("🔧 Reconstruction des phrases complètes...")
            segments = self.sentence_reconstructor.reconstruct_sentences(initial_segments)
            
            # Afficher les statistiques
            stats = self.sentence_reconstructor.get_reconstruction_stats(initial_segments, segments)
            print(f"   📊 {stats['original_segments']} segments → {stats['reconstructed_sentences']} phrases")
            print(f"   📉 Réduction: {stats['reduction_count']} segments (-{stats['reduction_percentage']}%)")
        else:
            segments = initial_segments
        
        # Détection d'intervenants
        speaker_info = self._detect_speakers_simple(audio_path, segments)
        
        # Assigner les intervenants aux segments
        segments_with_speakers = self._assign_speakers_to_segments(segments, speaker_info["speaker_segments"])
        
        # Obtenir les métadonnées audio
        duration = result.get("duration", 0)
        if duration == 0 and segments:
            duration = segments[-1]["end"]
        
        # Structurer le résultat final
        structured_result = {
            "metadata": {
                "file": audio_file.name,
                "path": str(audio_file.absolute()),
                "duration": duration,
                "language": self.language,
                "model": self.model_name,
                "transcription_date": datetime.now().isoformat(),
                "word_timestamps_enabled": word_timestamps,
                "speaker_detection_enabled": self.enable_speaker_detection,
                "speakers_detected": len(speaker_info["speakers"]),
                "detection_method": "acoustic_clustering" if CLUSTERING_AVAILABLE else "energy_based"
            },
            "speakers": speaker_info["speakers"],
            "transcription": {
                "text": result["text"].strip(),
                "segments": segments_with_speakers
            }
        }
        
        # Statistiques
        total_words = sum(len(seg.get("words", [])) for seg in segments_with_speakers)
        print(f"✅ Transcription terminée !")
        print(f"👥 Intervenants : {len(speaker_info['speakers'])}")
        print(f"🎬 Segments : {len(segments_with_speakers)}")
        print(f"🔤 Mots : {total_words}")
        
        return structured_result
    
    def _assign_speakers_to_segments(
        self, 
        segments: List[Dict], 
        speaker_segments: List[Dict]
    ) -> List[Dict]:
        """Assigne les intervenants aux segments."""
        
        # Créer un mapping segment_id -> speaker
        speaker_mapping = {}
        for speaker_seg in speaker_segments:
            speaker_mapping[speaker_seg["segment_id"]] = speaker_seg["speaker"]
        
        # Assigner les speakers
        for segment in segments:
            speaker = speaker_mapping.get(segment["id"], "Intervenant_1")
            segment["speaker"] = speaker
            
            # Assigner aussi aux mots
            for word in segment.get("words", []):
                word["speaker"] = speaker
        
        return segments


# Alias pour compatibilité
AudioTranscriberWithSpeakers = SimpleAudioTranscriberWithSpeakers