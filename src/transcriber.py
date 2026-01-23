"""
Gestionnaire de transcription audio utilisant Whisper AI.
Fournit les fonctionnalités de transcription avec timecodes précis.
"""

import whisper
import librosa
import numpy as np
import torch
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
import warnings
warnings.filterwarnings("ignore", category=UserWarning)


class AudioTranscriber:
    """Classe principale pour la transcription audio avec timecodes."""
    
    def __init__(self, model_name: str = "medium", language: str = "fr", device: str = None, verbose: bool = False):
        """
        Initialise le transcripteur audio.
        
        Args:
            model_name: Nom du modèle Whisper ("tiny", "base", "small", "medium", "large")
            language: Code de langue (ex: "fr" pour français)
            device: Dispositif de calcul ("cpu", "cuda", "mps", None pour auto-détection)
            verbose: Affichage détaillé
        """
        self.model_name = model_name
        self.language = language
        self.device = device
        self.verbose = verbose
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Charge le modèle Whisper avec optimisation GPU."""
        print(f"📥 Chargement du modèle Whisper '{self.model_name}'...")
        
        # Détecter le dispositif disponible (GPU Apple Silicon ou CPU)
        if self.device is None:
            device = self._get_optimal_device()
        else:
            device = self.device
            
        print(f"🖥️  Dispositif utilisé : {device}")
        
        try:
            self.model = whisper.load_model(self.model_name, device=device)
            self.actual_device = device
            print("✅ Modèle chargé avec succès !")
        except Exception as e:
            # Fallback vers CPU si erreur GPU
            print(f"⚠️  Erreur GPU, basculement vers CPU : {str(e)}")
            self.model = whisper.load_model(self.model_name, device="cpu")
            self.actual_device = "cpu"
            print("✅ Modèle chargé sur CPU !")
    
    def _get_optimal_device(self):
        """Détermine le meilleur dispositif disponible."""
        import torch
        
        # Vérifier si MPS (Metal Performance Shaders) est disponible sur Mac
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"  # GPU Apple Silicon
        # Vérifier CUDA pour les GPU NVIDIA
        elif torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
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
    
    def transcribe_with_timestamps(
        self, 
        audio_path: str, 
        word_timestamps: bool = True
    ) -> Dict[str, Any]:
        """
        Transcrit un fichier audio avec des timecodes précis.
        
        Args:
            audio_path: Chemin vers le fichier audio
            word_timestamps: Si True, inclut les timecodes au niveau des mots
            
        Returns:
            Dictionnaire structuré avec la transcription et les métadonnées
        """
        if self.model is None:
            self._load_model()
        
        # Obtenir les informations audio
        audio_info = self.get_audio_info(audio_path)
        
        print("🎯 Analyse et transcription en cours...")
        
        try:
            # Options de transcription
            options = {
                "language": self.language,
                "word_timestamps": word_timestamps,
                "verbose": False
            }
            
            # Effectuer la transcription
            result = self.model.transcribe(audio_path, **options)
            
            # Structurer les résultats
            structured_result = {
                "metadata": {
                    "file": audio_info["filename"],
                    "path": audio_info["path"],
                    "duration": audio_info["duration"],
                    "sample_rate": audio_info["sample_rate"],
                    "format": audio_info["format"],
                    "size_bytes": audio_info["size_bytes"],
                    "language": self.language,
                    "model": self.model_name,
                    "transcription_date": datetime.now().isoformat(),
                    "word_timestamps_enabled": word_timestamps
                },
                "transcription": {
                    "text": result["text"].strip(),
                    "segments": []
                }
            }
            
            # Traiter chaque segment
            for segment in result["segments"]:
                segment_data = {
                    "id": segment["id"],
                    "start": round(segment["start"], 3),
                    "end": round(segment["end"], 3),
                    "duration": round(segment["end"] - segment["start"], 3),
                    "text": segment["text"].strip(),
                    "words": []
                }
                
                # Ajouter les mots avec timecodes si disponibles
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
                
                structured_result["transcription"]["segments"].append(segment_data)
            
            return structured_result
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la transcription : {str(e)}")
    
    def transcribe_segment(
        self, 
        audio_path: str, 
        start_time: float, 
        end_time: float
    ) -> Dict[str, Any]:
        """
        Transcrit un segment spécifique d'un fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            start_time: Temps de début en secondes
            end_time: Temps de fin en secondes
            
        Returns:
            Dictionnaire avec la transcription du segment
        """
        # Charger et découper l'audio
        y, sr = librosa.load(
            audio_path, 
            offset=start_time, 
            duration=end_time - start_time,
            sr=16000  # Whisper utilise 16kHz
        )
        
        # Sauvegarder temporairement le segment
        temp_path = "/tmp/temp_segment.wav"
        import soundfile as sf
        sf.write(temp_path, y, sr)
        
        try:
            # Transcrire le segment
            result = self.transcribe_with_timestamps(temp_path)
            
            # Ajuster les timecodes pour correspondre au fichier original
            for segment in result["transcription"]["segments"]:
                segment["start"] += start_time
                segment["end"] += start_time
                
                for word in segment["words"]:
                    word["start"] += start_time
                    word["end"] += start_time
            
            return result
            
        finally:
            # Nettoyer le fichier temporaire
            Path(temp_path).unlink(missing_ok=True)