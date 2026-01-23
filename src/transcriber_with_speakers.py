"""
Gestionnaire de transcription audio utilisant Whisper AI avec détection d'intervenants.
Fournit les fonctionnalités de transcription avec timecodes précis et identification des locuteurs.
"""

import whisper
import librosa
import numpy as np
import torch
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

try:
    from pyannote.audio import Pipeline
    from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
    DIARIZATION_AVAILABLE = True
except ImportError:
    DIARIZATION_AVAILABLE = False
    print("⚠️  pyannote.audio non disponible. Détection d'intervenants désactivée.")


class AudioTranscriberWithSpeakers:
    """Classe principale pour la transcription audio avec timecodes et détection d'intervenants."""
    
    def __init__(
        self, 
        model_name: str = "medium", 
        language: str = "fr", 
        device: str = None, 
        enable_diarization: bool = True,
        verbose: bool = False
    ):
        """
        Initialise le transcripteur audio avec détection d'intervenants.
        
        Args:
            model_name: Nom du modèle Whisper ("tiny", "base", "small", "medium", "large")
            language: Code de langue (ex: "fr" pour français)
            device: Dispositif de calcul ("cpu", "cuda", "mps", None pour auto-détection)
            enable_diarization: Activer la détection d'intervenants
            verbose: Affichage détaillé
        """
        self.model_name = model_name
        self.language = language
        self.device = self._setup_device(device)
        self.enable_diarization = enable_diarization and DIARIZATION_AVAILABLE
        self.verbose = verbose
        self.model = None
        self.diarization_pipeline = None
        
        self._load_model()
        if self.enable_diarization:
            self._load_diarization_model()
    
    def _setup_device(self, device: Optional[str]) -> str:
        """
        Configure le dispositif de calcul optimal.
        
        Args:
            device: Dispositif demandé ou None pour auto-détection
            
        Returns:
            Nom du dispositif à utiliser
        """
        if device is not None:
            return device
        
        # Auto-détection du meilleur dispositif
        if torch.backends.mps.is_available():
            return "mps"  # Apple Silicon GPU
        elif torch.cuda.is_available():
            return "cuda"  # NVIDIA GPU
        else:
            return "cpu"
    
    def _load_model(self):
        """Charge le modèle Whisper avec optimisation GPU."""
        print(f"📥 Chargement du modèle Whisper '{self.model_name}' sur {self.device}...")
        
        try:
            # Forcer CPU pour éviter les erreurs MPS avec certaines opérations Whisper
            if self.device == "mps":
                print("⚠️  MPS détecté mais utilisation CPU pour compatibilité Whisper")
                self.device = "cpu"
            
            self.model = whisper.load_model(self.model_name, device=self.device)
            print("✅ Modèle Whisper chargé avec succès !")
        except Exception as e:
            print(f"⚠️  Erreur GPU, basculement vers CPU : {e}")
            self.device = "cpu"
            self.model = whisper.load_model(self.model_name, device="cpu")
    
    def _load_diarization_model(self):
        """Charge le modèle de détection d'intervenants."""
        if not DIARIZATION_AVAILABLE:
            print("⚠️  Détection d'intervenants non disponible")
            return
        
        print("📥 Chargement du modèle de détection d'intervenants...")
        try:
            # Utiliser le modèle pré-entraîné de pyannote
            self.diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1"
                # Suppression de use_auth_token obsolète
            )
            
            # Configurer le dispositif
            if self.device != "cpu":
                try:
                    self.diarization_pipeline.to(torch.device(self.device))
                except:
                    print("⚠️  Détection d'intervenants sur CPU")
            
            print("✅ Modèle de détection d'intervenants chargé !")
            
        except Exception as e:
            print(f"⚠️  Erreur chargement détection d'intervenants : {e}")
            self.enable_diarization = False
    
    def _perform_diarization(self, audio_path: str) -> Dict[str, Any]:
        """
        Effectue la détection d'intervenants sur le fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Dictionnaire avec les segments par intervenant
        """
        if not self.enable_diarization or self.diarization_pipeline is None:
            return {"speakers": {}, "segments": []}
        
        try:
            print("🎯 Détection des intervenants...")
            
            # Analyser le fichier audio
            diarization = self.diarization_pipeline(audio_path)
            
            # Organiser les résultats
            speakers = {}
            segments = []
            
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_id = f"Intervenant_{speaker}"
                
                if speaker_id not in speakers:
                    speakers[speaker_id] = {
                        "id": speaker_id,
                        "label": speaker,
                        "total_time": 0.0,
                        "segments_count": 0
                    }
                
                segment = {
                    "speaker": speaker_id,
                    "start": float(turn.start),
                    "end": float(turn.end),
                    "duration": float(turn.end - turn.start)
                }
                
                segments.append(segment)
                speakers[speaker_id]["total_time"] += segment["duration"]
                speakers[speaker_id]["segments_count"] += 1
            
            print(f"✅ {len(speakers)} intervenants détectés")
            
            return {
                "speakers": speakers,
                "segments": segments
            }
            
        except Exception as e:
            print(f"❌ Erreur détection d'intervenants : {e}")
            return {"speakers": {}, "segments": []}
    
    def _assign_speakers_to_words(
        self, 
        transcription_segments: List[Dict], 
        diarization_segments: List[Dict]
    ) -> List[Dict]:
        """
        Assigne les intervenants aux mots transcrits.
        
        Args:
            transcription_segments: Segments de la transcription Whisper
            diarization_segments: Segments de détection d'intervenants
            
        Returns:
            Segments enrichis avec informations d'intervenants
        """
        if not diarization_segments:
            return transcription_segments
        
        enriched_segments = []
        
        for segment in transcription_segments:
            segment_start = segment["start"]
            segment_end = segment["end"]
            
            # Trouver l'intervenant principal pour ce segment
            speaker_times = {}
            
            for diar_segment in diarization_segments:
                # Calculer l'overlap entre les segments
                overlap_start = max(segment_start, diar_segment["start"])
                overlap_end = min(segment_end, diar_segment["end"])
                overlap_duration = max(0, overlap_end - overlap_start)
                
                if overlap_duration > 0:
                    speaker = diar_segment["speaker"]
                    speaker_times[speaker] = speaker_times.get(speaker, 0) + overlap_duration
            
            # Déterminer l'intervenant principal
            if speaker_times:
                main_speaker = max(speaker_times, key=speaker_times.get)
            else:
                main_speaker = "Inconnu"
            
            # Enrichir le segment
            enriched_segment = segment.copy()
            enriched_segment["speaker"] = main_speaker
            enriched_segment["speaker_confidence"] = (
                speaker_times.get(main_speaker, 0) / segment["duration"] 
                if segment["duration"] > 0 else 0
            )
            
            # Enrichir les mots avec l'intervenant
            if "words" in segment:
                for word in enriched_segment["words"]:
                    word["speaker"] = main_speaker
            
            enriched_segments.append(enriched_segment)
        
        return enriched_segments
    
    def transcribe_with_speakers(
        self, 
        audio_path: str, 
        word_timestamps: bool = True
    ) -> Dict[str, Any]:
        """
        Transcrit un fichier audio avec détection d'intervenants.
        
        Args:
            audio_path: Chemin vers le fichier audio
            word_timestamps: Si True, inclut les timecodes au niveau des mots
            
        Returns:
            Dictionnaire structuré avec transcription et informations d'intervenants
        """
        if self.model is None:
            self._load_model()
        
        # Obtenir les informations audio
        try:
            from audio_processor import AudioProcessor
            processor = AudioProcessor()
            audio_info = processor.get_audio_features(audio_path)
        except ImportError:
            # Fallback basique si audio_processor n'est pas disponible
            import librosa
            y, sr = librosa.load(audio_path, sr=None)
            audio_info = {
                "duration": len(y) / sr,
                "sample_rate": sr
            }
        
        print(f"🎵 Analyse de : {Path(audio_path).name}")
        print("=" * 50)
        
        # Détection d'intervenants
        diarization_result = self._perform_diarization(audio_path)
        
        # Transcription Whisper
        print("🎯 Transcription en cours...")
        
        try:
            # Options de transcription
            options = {
                "language": self.language,
                "word_timestamps": word_timestamps,
                "verbose": self.verbose
            }
            
            # Effectuer la transcription
            result = self.model.transcribe(audio_path, **options)
            
            # Structurer les résultats de base
            structured_result = {
                "metadata": {
                    "file": Path(audio_path).name,
                    "path": str(Path(audio_path).absolute()),
                    "duration": audio_info.get("duration", 0),
                    "sample_rate": audio_info.get("sample_rate", 0),
                    "format": Path(audio_path).suffix.lower().replace(".", ""),
                    "language": self.language,
                    "model": self.model_name,
                    "device": self.device,
                    "transcription_date": datetime.now().isoformat(),
                    "word_timestamps_enabled": word_timestamps,
                    "speaker_diarization_enabled": self.enable_diarization,
                    "speakers_detected": len(diarization_result["speakers"])
                },
                "speakers": diarization_result["speakers"],
                "transcription": {
                    "text": result["text"].strip(),
                    "segments": []
                },
                "diarization_segments": diarization_result["segments"]
            }
            
            # Traiter chaque segment de transcription
            transcription_segments = []
            for segment in result["segments"]:
                segment_data = {
                    "id": segment["id"],
                    "start": round(segment["start"], 3),
                    "end": round(segment["end"], 3),
                    "duration": round(segment["end"] - segment["start"], 3),
                    "text": segment["text"].strip(),
                    "words": []
                }
                
                # Ajouter les mots avec timecodes
                if word_timestamps and "words" in segment:
                    for word_info in segment["words"]:
                        word_data = {
                            "word": word_info["word"].strip(),
                            "start": round(word_info["start"], 3),
                            "end": round(word_info["end"], 3),
                            "duration": round(word_info["end"] - word_info["start"], 3),
                            "confidence": round(word_info.get("probability", 0.0), 3)
                        }
                        segment_data["words"].append(word_data)
                
                transcription_segments.append(segment_data)
            
            # Assigner les intervenants aux segments
            enriched_segments = self._assign_speakers_to_words(
                transcription_segments, 
                diarization_result["segments"]
            )
            
            structured_result["transcription"]["segments"] = enriched_segments
            
            # Statistiques finales
            total_words = sum(len(seg.get("words", [])) for seg in enriched_segments)
            print(f"✅ Transcription terminée !")
            print(f"👥 Intervenants : {len(diarization_result['speakers'])}")
            print(f"🎬 Segments : {len(enriched_segments)}")
            print(f"🔤 Mots : {total_words}")
            
            return structured_result
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la transcription : {str(e)}")
    
    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        Récupère les informations sur le fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            
        Returns:
            Dictionnaire avec les métadonnées audio
        """
        try:
            # Charger l'audio avec librosa pour obtenir les métadonnées
            y, sr = librosa.load(audio_path, sr=None)
            duration = len(y) / sr
            
            audio_file = Path(audio_path)
            
            return {
                "filename": audio_file.name,
                "path": str(audio_file.absolute()),
                "duration": duration,
                "sample_rate": sr,
                "channels": 1 if len(y.shape) == 1 else y.shape[0],
                "size_bytes": audio_file.stat().st_size,
                "format": audio_file.suffix.lower().replace(".", "")
            }
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'analyse du fichier audio : {str(e)}")


# Garder la compatibilité avec l'ancien nom
AudioTranscriber = AudioTranscriberWithSpeakers