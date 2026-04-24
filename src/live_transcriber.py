"""
Transcription en direct avec Silero VAD et faster-whisper.

Accumule l'audio entrant dans un buffer, detecte les segments de parole
via Silero VAD, et lance la transcription sur chaque segment termine.
Les resultats sont transmis au fur et a mesure via un callback.
"""

import io
import logging
import tempfile
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

logger = logging.getLogger("scribe.live_transcriber")

# Audio constants
SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2  # 16-bit PCM
CHANNELS = 1

# VAD thresholds
DEFAULT_VAD_THRESHOLD = 0.5
DEFAULT_MIN_SPEECH_MS = 250
DEFAULT_MIN_SILENCE_MS = 700
DEFAULT_MAX_SEGMENT_S = 30.0
DEFAULT_PADDING_MS = 300


@dataclass
class LiveSegment:
    """Un segment de parole detecte et transcrit."""

    id: int
    start: float
    end: float
    text: str
    words: List[Dict[str, Any]] = field(default_factory=list)
    is_partial: bool = False
    speaker: Optional[str] = None
    semantic_analysis: Optional[Dict[str, float]] = None


@dataclass
class LiveTranscriberConfig:
    """Configuration du transcripteur live."""

    vad_threshold: float = DEFAULT_VAD_THRESHOLD
    min_speech_ms: int = DEFAULT_MIN_SPEECH_MS
    min_silence_ms: int = DEFAULT_MIN_SILENCE_MS
    max_segment_seconds: float = DEFAULT_MAX_SEGMENT_S
    padding_ms: int = DEFAULT_PADDING_MS
    language: str = "fr"
    with_semantic_analysis: bool = False


class LiveTranscriber:
    """
    Transcripteur en temps reel.

    Utilise Silero VAD pour detecter la parole, puis faster-whisper
    pour transcrire chaque segment detecte.
    """

    def __init__(
        self,
        transcriber: Any,
        semantic_analyzer: Optional[Any] = None,
        config: Optional[LiveTranscriberConfig] = None,
    ):
        """
        Initialise le transcripteur live.

        Args:
            transcriber: Instance de FastTranscriber ou AudioTranscriber
            semantic_analyzer: Instance optionnelle d'analyseur semantique
            config: Configuration du live transcriber
        """
        self.transcriber = transcriber
        self.semantic_analyzer = semantic_analyzer
        self.config = config or LiveTranscriberConfig()

        # Silero VAD
        self._vad_model = None
        self._load_vad()

        # State
        self._audio_buffer = np.array([], dtype=np.float32)
        self._session_start = 0.0
        self._total_samples = 0
        self._segment_counter = 0
        self._is_speaking = False
        self._speech_start_sample = 0
        self._silence_samples = 0
        self._active = False

    def _load_vad(self):
        """Charge le modele Silero VAD depuis torch.hub."""
        import torch

        logger.info("Chargement Silero VAD...")
        start = time.time()

        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False,
        )
        self._vad_model = model
        self._vad_get_speech_timestamps = utils[0]  # get_speech_timestamps
        self._vad_read_audio = utils[2]  # read_audio

        elapsed = time.time() - start
        logger.info("Silero VAD charge en %.1fs", elapsed)

    def reset(self):
        """Reinitialise l'etat pour une nouvelle session."""
        self._audio_buffer = np.array([], dtype=np.float32)
        self._session_start = time.time()
        self._total_samples = 0
        self._segment_counter = 0
        self._is_speaking = False
        self._speech_start_sample = 0
        self._silence_samples = 0
        self._active = True

        if self._vad_model is not None:
            self._vad_model.reset_states()

        logger.info("Live transcriber reset, nouvelle session")

    def stop(self):
        """Arrete la session en cours."""
        self._active = False

    @property
    def elapsed_time(self) -> float:
        """Temps ecoule depuis le debut de la session."""
        return self._total_samples / SAMPLE_RATE

    def process_audio_chunk(
        self,
        audio_data: bytes,
    ) -> List[LiveSegment]:
        """
        Traite un chunk d'audio PCM 16-bit mono 16kHz.

        Args:
            audio_data: Bytes PCM 16-bit, mono, 16kHz

        Returns:
            Liste de segments transcrits (peut etre vide si pas assez de parole)
        """
        if not self._active:
            return []

        # Convertir bytes PCM en float32 [-1, 1]
        pcm = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

        # Ajouter au buffer global
        self._audio_buffer = np.concatenate([self._audio_buffer, pcm])
        self._total_samples += len(pcm)

        # Detecter les segments de parole avec VAD
        return self._detect_and_transcribe()

    def _detect_and_transcribe(self) -> List[LiveSegment]:
        """Detecte la parole dans le buffer et transcrit les segments termines."""
        import torch

        results = []

        # Taille minimale pour VAD: 512 samples (32ms a 16kHz)
        if len(self._audio_buffer) < 512:
            return results

        # Passer le dernier chunk au VAD pour decision frame-level
        # Silero VAD attend des chunks de 512 samples (32ms)
        chunk_size = 512
        buffer_len = len(self._audio_buffer)

        # On traite les samples non encore analyses
        process_start = max(0, buffer_len - chunk_size * 4)  # Last ~128ms
        chunk = self._audio_buffer[process_start:buffer_len]

        if len(chunk) < chunk_size:
            return results

        # Obtenir la probabilite de parole sur le chunk
        tensor = torch.FloatTensor(chunk[-chunk_size:])
        speech_prob = self._vad_model(tensor, SAMPLE_RATE).item()

        is_speech = speech_prob >= self.config.vad_threshold
        min_silence_samples = int(self.config.min_silence_ms * SAMPLE_RATE / 1000)
        min_speech_samples = int(self.config.min_speech_ms * SAMPLE_RATE / 1000)
        max_segment_samples = int(self.config.max_segment_seconds * SAMPLE_RATE)
        padding_samples = int(self.config.padding_ms * SAMPLE_RATE / 1000)

        if is_speech:
            self._silence_samples = 0
            if not self._is_speaking:
                # Debut de parole
                self._is_speaking = True
                self._speech_start_sample = max(
                    0, self._total_samples - len(chunk) - padding_samples
                )
        else:
            if self._is_speaking:
                self._silence_samples += chunk_size

                # Assez de silence pour considerer la fin du segment ?
                if self._silence_samples >= min_silence_samples:
                    speech_end_sample = (
                        self._total_samples
                        - self._silence_samples
                        + padding_samples
                    )
                    speech_duration = (
                        speech_end_sample - self._speech_start_sample
                    )

                    if speech_duration >= min_speech_samples:
                        segment = self._transcribe_segment(
                            self._speech_start_sample,
                            speech_end_sample,
                        )
                        if segment is not None:
                            results.append(segment)

                    self._is_speaking = False
                    self._silence_samples = 0

        # Forcer la transcription si le segment est trop long
        if self._is_speaking:
            current_duration = self._total_samples - self._speech_start_sample
            if current_duration >= max_segment_samples:
                segment = self._transcribe_segment(
                    self._speech_start_sample,
                    self._total_samples,
                )
                if segment is not None:
                    results.append(segment)
                self._speech_start_sample = self._total_samples
                self._is_speaking = False
                self._silence_samples = 0

        # Garder seulement le buffer necessaire (ne pas accumuler indefiniment)
        keep_from = self._speech_start_sample if self._is_speaking else max(
            0, self._total_samples - SAMPLE_RATE  # Garder 1s de contexte
        )
        # Convertir en index relatif au buffer
        buffer_offset = self._total_samples - len(self._audio_buffer)
        trim_index = max(0, keep_from - buffer_offset)
        if trim_index > 0:
            self._audio_buffer = self._audio_buffer[trim_index:]

        return results

    def _transcribe_segment(
        self,
        start_sample: int,
        end_sample: int,
    ) -> Optional[LiveSegment]:
        """Transcrit un segment audio detecte par VAD."""
        # Extraire l'audio du buffer
        buffer_offset = self._total_samples - len(self._audio_buffer)
        buf_start = max(0, start_sample - buffer_offset)
        buf_end = min(len(self._audio_buffer), end_sample - buffer_offset)

        if buf_end <= buf_start:
            return None

        audio_segment = self._audio_buffer[buf_start:buf_end]

        if len(audio_segment) < SAMPLE_RATE * 0.1:  # Moins de 100ms
            return None

        # Sauvegarder en WAV temporaire pour Whisper
        tmp = tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False, prefix="live_"
        )
        try:
            with wave.open(tmp.name, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(SAMPLE_WIDTH)
                wf.setframerate(SAMPLE_RATE)
                pcm_int16 = (audio_segment * 32768).astype(np.int16)
                wf.writeframes(pcm_int16.tobytes())

            # Transcrire
            start_time_s = start_sample / SAMPLE_RATE
            end_time_s = end_sample / SAMPLE_RATE

            logger.debug(
                "Transcription segment %.1f-%.1fs (%.1fs)",
                start_time_s,
                end_time_s,
                end_time_s - start_time_s,
            )

            if hasattr(self.transcriber, "transcribe_with_timestamps"):
                result = self.transcriber.transcribe_with_timestamps(
                    tmp.name, word_timestamps=True
                )
            else:
                return None

            transcription = result.get("transcription", {})
            text = transcription.get("text", "").strip()

            if not text:
                return None

            # Construire les mots avec timecodes absolus
            words = []
            for seg in transcription.get("segments", []):
                for w in seg.get("words", []):
                    words.append(
                        {
                            "word": w["word"],
                            "start": round(start_time_s + w["start"], 3),
                            "end": round(start_time_s + w["end"], 3),
                            "confidence": w.get("confidence", 0),
                        }
                    )

            self._segment_counter += 1

            segment = LiveSegment(
                id=self._segment_counter,
                start=round(start_time_s, 3),
                end=round(end_time_s, 3),
                text=text,
                words=words,
                is_partial=False,
            )

            # Analyse semantique optionnelle
            if (
                self.config.with_semantic_analysis
                and self.semantic_analyzer is not None
            ):
                try:
                    scores = self.semantic_analyzer.analyze_segment(text)
                    if scores:
                        segment.semantic_analysis = scores
                except Exception as e:
                    logger.debug("Semantic analysis failed for segment: %s", e)

            logger.info(
                "Segment #%d [%.1f-%.1fs]: %s",
                segment.id,
                segment.start,
                segment.end,
                text[:80],
            )

            return segment

        except Exception as e:
            logger.warning("Transcription segment failed: %s", e)
            return None

        finally:
            Path(tmp.name).unlink(missing_ok=True)

    def flush(self) -> List[LiveSegment]:
        """
        Force la transcription de tout audio restant dans le buffer.

        Appeler a la fin d'une session pour traiter le dernier segment
        si l'utilisateur s'est arrete de parler sans silence suffisant.
        """
        results = []

        if self._is_speaking and self._total_samples > self._speech_start_sample:
            segment = self._transcribe_segment(
                self._speech_start_sample,
                self._total_samples,
            )
            if segment is not None:
                results.append(segment)

        self._is_speaking = False
        self._silence_samples = 0

        return results
