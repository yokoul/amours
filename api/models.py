"""
Singleton holder for ML models loaded once at startup.

All heavy models (Whisper, sentence-transformers, etc.) are loaded here
and shared across all request handlers via the global `models` instance.
"""

import gc
import logging
import time

logger = logging.getLogger("scribe.models")


class ModelRegistry:
    """Holds references to all loaded ML models and heavy resources."""

    def __init__(self):
        self.transcriber = None
        self.semantic_analyzer = None
        self.sentence_reconstructor = None
        self.mix_player = None
        self.audio_processor = None
        self.video_processor = None
        self._whisper_backend = None
        self._ready = False
        self._load_times = {}

    @property
    def ready(self) -> bool:
        return self._ready

    def load_all(
        self,
        whisper_model: str = "medium",
        whisper_language: str = "fr",
        whisper_device: str = "",
        whisper_backend: str = "auto",
        semantic_threshold: float = 0.1,
        transcription_dir: str = "output_transcription",
        audio_dir: str = "audio",
    ):
        """Load all models. Called once at server startup."""
        logger.info("Loading models...")
        total_start = time.time()

        self._load_transcriber(
            whisper_model, whisper_language, whisper_device, whisper_backend
        )
        self._load_semantic_analyzer(semantic_threshold)
        self._load_sentence_reconstructor()
        self._load_mix_player(transcription_dir, audio_dir)
        self._load_audio_processor()
        self._load_video_processor()

        self._ready = True
        total_elapsed = time.time() - total_start
        logger.info("All models loaded in %.1fs", total_elapsed)
        for name, elapsed in self._load_times.items():
            logger.info("  %s: %.1fs", name, elapsed)

    def _release_transcriber(self):
        """Free the current transcriber and reclaim GPU/CPU memory."""
        if self.transcriber is None:
            return
        old_backend = self._whisper_backend or "unknown"
        # Drop model references
        if hasattr(self.transcriber, "model"):
            del self.transcriber.model
        if hasattr(self.transcriber, "diarization_pipeline"):
            del self.transcriber.diarization_pipeline
        self.transcriber = None
        self._whisper_backend = None
        # Force garbage collection to reclaim memory
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        logger.info("Released previous transcriber (%s), memory freed", old_backend)

    def _load_transcriber(
        self, model_name: str, language: str, device: str, backend: str = "auto"
    ):
        start = time.time()
        device_arg = device if device else None

        # Release any previously loaded transcriber before loading a new one
        self._release_transcriber()

        # Determine backend: auto prefers faster-whisper when available
        use_faster = False
        if backend in ("auto", "faster-whisper"):
            try:
                import faster_whisper  # noqa: F401

                use_faster = True
            except ImportError:
                if backend == "faster-whisper":
                    logger.error(
                        "faster-whisper requested but not installed. "
                        "Install with: pip install faster-whisper"
                    )
                else:
                    logger.info("faster-whisper not available, using openai-whisper")

        if use_faster:
            try:
                from src.fast_transcriber import FastTranscriber

                self.transcriber = FastTranscriber(
                    model_name=model_name,
                    language=language,
                    device=device_arg,
                    enable_diarization=True,
                    verbose=False,
                )
                self._whisper_backend = "faster-whisper"
                logger.info(
                    "faster-whisper '%s' loaded on %s (%s)",
                    model_name,
                    self.transcriber.device,
                    self.transcriber.compute_type,
                )
                self._load_times["transcriber"] = time.time() - start
                return
            except Exception as e:
                logger.warning("Failed to load faster-whisper: %s", e)

        # Fallback: openai-whisper
        try:
            from src.transcriber_with_speakers import AudioTranscriberWithSpeakers

            self.transcriber = AudioTranscriberWithSpeakers(
                model_name=model_name,
                language=language,
                device=device_arg,
                enable_diarization=True,
                verbose=False,
            )
            self._whisper_backend = "openai-whisper"
            logger.info(
                "openai-whisper '%s' loaded on %s",
                model_name,
                getattr(self.transcriber, "device", "unknown"),
            )
        except Exception as e:
            logger.warning("Failed to load transcriber with speakers: %s", e)
            try:
                from src.transcriber import AudioTranscriber

                self.transcriber = AudioTranscriber(
                    model_name=model_name,
                    language=language,
                    device=device_arg,
                    verbose=False,
                )
                self._whisper_backend = "openai-whisper"
                logger.info("Loaded basic transcriber (no speaker diarization)")
            except Exception as e2:
                logger.error("Failed to load any transcriber: %s", e2)
                self._whisper_backend = None
        self._load_times["transcriber"] = time.time() - start

    def _load_semantic_analyzer(self, threshold: float):
        start = time.time()
        try:
            from src.love_analyzer import LoveTypeAnalyzer

            self.semantic_analyzer = LoveTypeAnalyzer(
                min_score_threshold=threshold,
                use_semantic_analysis=True,
                reconstruct_sentences=False,
            )
            logger.info("SemanticAnalyzer loaded")
        except Exception as e:
            logger.error("Failed to load semantic analyzer: %s", e)
        self._load_times["semantic_analyzer"] = time.time() - start

    def _load_sentence_reconstructor(self):
        start = time.time()
        try:
            from src.sentence_reconstructor import SentenceReconstructor

            self.sentence_reconstructor = SentenceReconstructor()
            logger.info("SentenceReconstructor loaded")
        except Exception as e:
            logger.error("Failed to load sentence reconstructor: %s", e)
        self._load_times["sentence_reconstructor"] = time.time() - start

    def _load_mix_player(self, transcription_dir: str, audio_dir: str):
        start = time.time()
        try:
            from src.mix_player import MixPlayer

            self.mix_player = MixPlayer(
                transcription_dir=transcription_dir,
                audio_dir=audio_dir,
            )
            self.mix_player.load_transcriptions()
            word_count = len(self.mix_player.word_index) if hasattr(self.mix_player, "word_index") else 0
            logger.info("MixPlayer loaded, %d words indexed", word_count)
        except Exception as e:
            logger.warning("Failed to load MixPlayer: %s", e)
        self._load_times["mix_player"] = time.time() - start

    def _load_audio_processor(self):
        start = time.time()
        try:
            from src.audio_processor import AudioProcessor

            self.audio_processor = AudioProcessor(target_sr=16000)
            logger.info("AudioProcessor loaded")
        except Exception as e:
            logger.error("Failed to load audio processor: %s", e)
        self._load_times["audio_processor"] = time.time() - start

    def _load_video_processor(self):
        start = time.time()
        try:
            from src.video_processor import VideoProcessor

            self.video_processor = VideoProcessor(thumbnail_width=320)
            logger.info("VideoProcessor loaded")
        except ImportError:
            logger.info("VideoProcessor unavailable (PyAV not installed)")
        except Exception as e:
            logger.warning("Failed to load video processor: %s", e)
        self._load_times["video_processor"] = time.time() - start

    def reload_mix_player_index(self):
        """Reload Mix-Play word index after new transcriptions are added."""
        if self.mix_player is not None:
            self.mix_player.load_transcriptions()
            word_count = len(self.mix_player.word_index) if hasattr(self.mix_player, "word_index") else 0
            logger.info("MixPlayer index reloaded, %d words indexed", word_count)


# Global singleton
models = ModelRegistry()
