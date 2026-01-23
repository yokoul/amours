"""
Processeur audio pour le prétraitement des fichiers avant transcription.
Gère la conversion de formats et l'optimisation des fichiers audio.
"""

import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List
from pydub import AudioSegment
import tempfile


class AudioProcessor:
    """Classe pour le traitement et la préparation des fichiers audio."""
    
    def __init__(self, target_sr: int = 16000):
        """
        Initialise le processeur audio.
        
        Args:
            target_sr: Fréquence d'échantillonnage cible (Whisper utilise 16kHz)
        """
        self.target_sr = target_sr
    
    def convert_to_wav(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Convertit un fichier audio vers le format WAV.
        
        Args:
            input_path: Chemin du fichier audio d'entrée
            output_path: Chemin de sortie (optionnel)
            
        Returns:
            Chemin du fichier WAV créé
        """
        input_file = Path(input_path)
        
        if output_path is None:
            output_path = input_file.with_suffix('.wav')
        
        try:
            # Utiliser pydub pour la conversion
            audio = AudioSegment.from_file(input_path)
            
            # Convertir en mono si stéréo
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Ajuster la fréquence d'échantillonnage
            if audio.frame_rate != self.target_sr:
                audio = audio.set_frame_rate(self.target_sr)
            
            # Exporter en WAV
            audio.export(output_path, format="wav")
            
            print(f"✅ Conversion terminée : {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la conversion audio : {str(e)}")
    
    def normalize_audio(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """
        Normalise l'audio pour améliorer la qualité de transcription.
        
        Args:
            audio_path: Chemin du fichier audio
            output_path: Chemin de sortie (optionnel)
            
        Returns:
            Chemin du fichier normalisé
        """
        if output_path is None:
            input_file = Path(audio_path)
            output_path = input_file.with_name(f"{input_file.stem}_normalized{input_file.suffix}")
        
        try:
            # Charger l'audio
            y, sr = librosa.load(audio_path, sr=self.target_sr)
            
            # Normalisation RMS
            y_normalized = librosa.util.normalize(y)
            
            # Réduction du bruit simple (filtrage)
            y_filtered = self._simple_noise_reduction(y_normalized, sr)
            
            # Sauvegarder
            sf.write(output_path, y_filtered, sr)
            
            print(f"✅ Normalisation terminée : {output_path}")
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la normalisation : {str(e)}")
    
    def _simple_noise_reduction(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Applique une réduction de bruit simple.
        
        Args:
            y: Signal audio
            sr: Fréquence d'échantillonnage
            
        Returns:
            Signal audio filtré
        """
        # Filtrage passe-haut pour réduire les bruits de basse fréquence
        y_filtered = librosa.effects.preemphasis(y)
        
        # Trim silence au début et à la fin
        y_trimmed, _ = librosa.effects.trim(y_filtered, top_db=20)
        
        return y_trimmed
    
    def split_audio_by_silence(
        self, 
        audio_path: str, 
        min_silence_len: int = 1000,
        silence_thresh: int = -40
    ) -> List[Tuple[float, float]]:
        """
        Divise l'audio en segments basés sur les silences.
        
        Args:
            audio_path: Chemin du fichier audio
            min_silence_len: Durée minimale de silence en ms
            silence_thresh: Seuil de silence en dB
            
        Returns:
            Liste des segments (start_time, end_time) en secondes
        """
        try:
            # Charger avec pydub pour la détection de silence
            audio = AudioSegment.from_file(audio_path)
            
            # Détecter les chunks séparés par le silence
            chunks = self._detect_nonsilent_chunks(
                audio, min_silence_len, silence_thresh
            )
            
            # Convertir en secondes
            segments = []
            for start_ms, end_ms in chunks:
                start_sec = start_ms / 1000.0
                end_sec = end_ms / 1000.0
                segments.append((start_sec, end_sec))
            
            print(f"📊 {len(segments)} segments détectés")
            return segments
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la segmentation : {str(e)}")
    
    def _detect_nonsilent_chunks(
        self, 
        audio: AudioSegment, 
        min_silence_len: int, 
        silence_thresh: int
    ) -> List[Tuple[int, int]]:
        """
        Détecte les chunks non-silencieux dans l'audio.
        
        Args:
            audio: Segment audio (pydub)
            min_silence_len: Durée minimale de silence en ms
            silence_thresh: Seuil de silence en dB
            
        Returns:
            Liste des chunks (start_ms, end_ms)
        """
        # Utiliser pydub pour détecter les silences
        from pydub.silence import detect_nonsilent
        
        nonsilent_chunks = detect_nonsilent(
            audio,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh
        )
        
        return nonsilent_chunks
    
    def extract_segment(
        self, 
        audio_path: str, 
        start_time: float, 
        end_time: float,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extrait un segment spécifique d'un fichier audio.
        
        Args:
            audio_path: Chemin du fichier audio source
            start_time: Temps de début en secondes
            end_time: Temps de fin en secondes
            output_path: Chemin de sortie (optionnel)
            
        Returns:
            Chemin du segment extrait
        """
        if output_path is None:
            input_file = Path(audio_path)
            output_path = input_file.with_name(
                f"{input_file.stem}_{start_time:.1f}_{end_time:.1f}{input_file.suffix}"
            )
        
        try:
            # Charger et extraire le segment
            y, sr = librosa.load(
                audio_path,
                offset=start_time,
                duration=end_time - start_time,
                sr=self.target_sr
            )
            
            # Sauvegarder le segment
            sf.write(output_path, y, sr)
            
            return str(output_path)
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'extraction : {str(e)}")
    
    def get_audio_features(self, audio_path: str) -> dict:
        """
        Analyse les caractéristiques d'un fichier audio.
        
        Args:
            audio_path: Chemin du fichier audio
            
        Returns:
            Dictionnaire des caractéristiques audio
        """
        try:
            # Charger l'audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Calculer les caractéristiques
            duration = len(y) / sr
            rms = np.sqrt(np.mean(y**2))
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            
            return {
                "duration": duration,
                "sample_rate": sr,
                "rms_energy": float(rms),
                "spectral_centroid_mean": float(np.mean(spectral_centroid)),
                "zero_crossing_rate_mean": float(np.mean(zero_crossing_rate)),
                "dynamic_range": float(np.max(y) - np.min(y))
            }
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'analyse audio : {str(e)}")