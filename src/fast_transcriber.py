"""
Transcripteur audio utilisant faster-whisper (CTranslate2).

Fournit la meme interface que AudioTranscriber et AudioTranscriberWithSpeakers
mais avec un backend ~4x plus rapide grace a CTranslate2 (int8/float16).
Fonctionne sur CPU et GPU.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

try:
    from faster_whisper import WhisperModel

    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from pyannote.audio import Pipeline

    DIARIZATION_AVAILABLE = True
except ImportError:
    DIARIZATION_AVAILABLE = False

logger = logging.getLogger("scribe.fast_transcriber")


def _get_optimal_device() -> str:
    """Determine le meilleur dispositif disponible."""
    if not TORCH_AVAILABLE:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _compute_type_for_device(device: str) -> str:
    """Choisit le compute_type optimal selon le dispositif."""
    if device == "cuda":
        return "float16"
    return "int8"


class FastTranscriber:
    """
    Transcripteur audio utilisant faster-whisper (CTranslate2).

    Expose les memes methodes que AudioTranscriber et
    AudioTranscriberWithSpeakers pour etre un drop-in replacement.
    """

    def __init__(
        self,
        model_name: str = "medium",
        language: str = "fr",
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        enable_diarization: bool = True,
        verbose: bool = False,
    ):
        """
        Initialise le transcripteur faster-whisper.

        Args:
            model_name: Modele Whisper (tiny, base, small, medium, large-v2, large-v3)
            language: Code de langue (ex: "fr")
            device: Dispositif ("cpu", "cuda", None pour auto-detection)
            compute_type: Type de calcul ("int8", "float16", "float32", None pour auto)
            enable_diarization: Activer la detection d'intervenants via pyannote
            verbose: Affichage detaille
        """
        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper n'est pas installe. "
                "Installez-le avec: pip install faster-whisper"
            )

        self.model_name = model_name
        self.language = language
        self.device = device or _get_optimal_device()
        self.compute_type = compute_type or _compute_type_for_device(self.device)
        self.enable_diarization = enable_diarization and DIARIZATION_AVAILABLE
        self.verbose = verbose
        self.model = None
        self.diarization_pipeline = None

        self._load_model()
        if self.enable_diarization:
            self._load_diarization_model()

    def _load_model(self):
        """Charge le modele faster-whisper."""
        logger.info(
            "Chargement faster-whisper '%s' sur %s (%s)...",
            self.model_name,
            self.device,
            self.compute_type,
        )
        start = time.time()

        try:
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
            elapsed = time.time() - start
            logger.info("faster-whisper charge en %.1fs", elapsed)
        except Exception as e:
            if self.device != "cpu":
                logger.warning(
                    "Erreur %s, basculement vers CPU int8: %s", self.device, e
                )
                self.device = "cpu"
                self.compute_type = "int8"
                self.model = WhisperModel(
                    self.model_name, device="cpu", compute_type="int8"
                )
                logger.info("faster-whisper charge sur CPU (fallback)")
            else:
                raise

    def _load_diarization_model(self):
        """Charge le modele de detection d'intervenants pyannote."""
        if not DIARIZATION_AVAILABLE:
            return

        logger.info("Chargement du modele de diarisation...")
        try:
            self.diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1"
            )
            if self.device == "cuda" and TORCH_AVAILABLE:
                try:
                    self.diarization_pipeline.to(torch.device("cuda"))
                except Exception:
                    logger.warning("Diarisation sur CPU")
            logger.info("Modele de diarisation charge")
        except Exception as e:
            logger.warning("Diarisation indisponible: %s", e)
            self.enable_diarization = False

    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        Recupere les informations sur le fichier audio.

        Args:
            audio_path: Chemin vers le fichier audio

        Returns:
            Dictionnaire avec les metadonnees audio
        """
        import librosa

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
            "format": audio_file.suffix.lower().replace(".", ""),
        }

    def transcribe_with_timestamps(
        self,
        audio_path: str,
        word_timestamps: bool = True,
    ) -> Dict[str, Any]:
        """
        Transcrit un fichier audio avec timecodes precis.

        Interface compatible avec AudioTranscriber.transcribe_with_timestamps.

        Args:
            audio_path: Chemin vers le fichier audio
            word_timestamps: Si True, inclut les timecodes au niveau des mots

        Returns:
            Dictionnaire structure avec la transcription et les metadonnees
        """
        if self.model is None:
            self._load_model()

        audio_info = self.get_audio_info(audio_path)

        logger.info("Transcription faster-whisper: %s", Path(audio_path).name)
        start = time.time()

        segments_gen, info = self.model.transcribe(
            audio_path,
            language=self.language,
            word_timestamps=word_timestamps,
            vad_filter=True,
        )

        # Materialiser le generateur et structurer les resultats
        segments = []
        full_text_parts = []

        for seg in segments_gen:
            segment_data = {
                "id": seg.id,
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "duration": round(seg.end - seg.start, 3),
                "text": seg.text.strip(),
                "words": [],
            }

            if word_timestamps and seg.words:
                for w in seg.words:
                    segment_data["words"].append(
                        {
                            "word": w.word.strip(),
                            "start": round(w.start, 3),
                            "end": round(w.end, 3),
                            "duration": round(w.end - w.start, 3),
                            "confidence": round(w.probability, 3),
                        }
                    )

            segments.append(segment_data)
            full_text_parts.append(seg.text.strip())

        elapsed = time.time() - start
        logger.info(
            "Transcription terminee en %.1fs (%d segments, ratio %.1fx)",
            elapsed,
            len(segments),
            audio_info["duration"] / elapsed if elapsed > 0 else 0,
        )

        return {
            "metadata": {
                "file": audio_info["filename"],
                "path": audio_info["path"],
                "duration": audio_info["duration"],
                "sample_rate": audio_info["sample_rate"],
                "format": audio_info["format"],
                "size_bytes": audio_info["size_bytes"],
                "language": info.language,
                "language_probability": round(info.language_probability, 3),
                "model": self.model_name,
                "backend": "faster-whisper",
                "device": self.device,
                "compute_type": self.compute_type,
                "transcription_date": datetime.now().isoformat(),
                "word_timestamps_enabled": word_timestamps,
                "transcription_duration_seconds": round(elapsed, 2),
            },
            "transcription": {
                "text": " ".join(full_text_parts),
                "segments": segments,
            },
        }

    def transcribe_with_speakers(
        self,
        audio_path: str,
        word_timestamps: bool = True,
    ) -> Dict[str, Any]:
        """
        Transcrit un fichier audio avec detection d'intervenants.

        Interface compatible avec AudioTranscriberWithSpeakers.transcribe_with_speakers.

        Args:
            audio_path: Chemin vers le fichier audio
            word_timestamps: Si True, inclut les timecodes au niveau des mots

        Returns:
            Dictionnaire structure avec transcription et informations d'intervenants
        """
        # Transcription de base
        result = self.transcribe_with_timestamps(audio_path, word_timestamps)

        # Diarisation
        diarization_result = self._perform_diarization(audio_path)

        # Enrichir les segments avec les intervenants
        segments = result["transcription"]["segments"]
        enriched_segments = self._assign_speakers_to_words(
            segments, diarization_result["segments"]
        )
        result["transcription"]["segments"] = enriched_segments

        # Ajouter les metadonnees de diarisation
        result["metadata"]["speaker_diarization_enabled"] = self.enable_diarization
        result["metadata"]["speakers_detected"] = len(diarization_result["speakers"])
        result["speakers"] = diarization_result["speakers"]
        result["diarization_segments"] = diarization_result["segments"]

        return result

    def _perform_diarization(self, audio_path: str) -> Dict[str, Any]:
        """Effectue la detection d'intervenants."""
        if not self.enable_diarization or self.diarization_pipeline is None:
            return {"speakers": {}, "segments": []}

        try:
            logger.info("Detection des intervenants...")
            diarization = self.diarization_pipeline(audio_path)

            speakers = {}
            segments = []

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_id = f"Intervenant_{speaker}"

                if speaker_id not in speakers:
                    speakers[speaker_id] = {
                        "id": speaker_id,
                        "label": speaker,
                        "total_time": 0.0,
                        "segments_count": 0,
                    }

                segment = {
                    "speaker": speaker_id,
                    "start": float(turn.start),
                    "end": float(turn.end),
                    "duration": float(turn.end - turn.start),
                }

                segments.append(segment)
                speakers[speaker_id]["total_time"] += segment["duration"]
                speakers[speaker_id]["segments_count"] += 1

            logger.info("%d intervenants detectes", len(speakers))
            return {"speakers": speakers, "segments": segments}

        except Exception as e:
            logger.warning("Erreur diarisation: %s", e)
            return {"speakers": {}, "segments": []}

    def _assign_speakers_to_words(
        self,
        transcription_segments: List[Dict],
        diarization_segments: List[Dict],
    ) -> List[Dict]:
        """Assigne les intervenants aux mots transcrits."""
        if not diarization_segments:
            return transcription_segments

        enriched_segments = []

        for segment in transcription_segments:
            seg_start = segment["start"]
            seg_end = segment["end"]

            # Trouver l'intervenant principal par overlap maximal
            speaker_times = {}
            for diar_seg in diarization_segments:
                overlap_start = max(seg_start, diar_seg["start"])
                overlap_end = min(seg_end, diar_seg["end"])
                overlap = max(0, overlap_end - overlap_start)

                if overlap > 0:
                    speaker = diar_seg["speaker"]
                    speaker_times[speaker] = speaker_times.get(speaker, 0) + overlap

            main_speaker = (
                max(speaker_times, key=speaker_times.get)
                if speaker_times
                else "Inconnu"
            )

            enriched = segment.copy()
            enriched["speaker"] = main_speaker
            enriched["speaker_confidence"] = (
                speaker_times.get(main_speaker, 0) / segment["duration"]
                if segment["duration"] > 0
                else 0
            )

            if "words" in segment:
                enriched["words"] = [
                    {**w, "speaker": main_speaker} for w in segment["words"]
                ]

            enriched_segments.append(enriched)

        return enriched_segments

    def transcribe_segment(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
    ) -> Dict[str, Any]:
        """
        Transcrit un segment specifique d'un fichier audio.

        Args:
            audio_path: Chemin vers le fichier audio
            start_time: Temps de debut en secondes
            end_time: Temps de fin en secondes

        Returns:
            Dictionnaire avec la transcription du segment
        """
        import librosa
        import soundfile as sf

        y, sr = librosa.load(
            audio_path,
            offset=start_time,
            duration=end_time - start_time,
            sr=16000,
        )

        temp_path = "/tmp/temp_segment_fast.wav"
        sf.write(temp_path, y, sr)

        try:
            result = self.transcribe_with_timestamps(temp_path)

            # Ajuster les timecodes
            for segment in result["transcription"]["segments"]:
                segment["start"] += start_time
                segment["end"] += start_time
                for word in segment.get("words", []):
                    word["start"] += start_time
                    word["end"] += start_time

            return result
        finally:
            Path(temp_path).unlink(missing_ok=True)
