"""
Singleton holder for ML models loaded once at startup.

All heavy models (Whisper, sentence-transformers, etc.) are loaded here
and shared across all request handlers via the global `models` instance.
"""

import logging
import time

logger = logging.getLogger("amours.models")


class ModelRegistry:
    """Holds references to all loaded ML models and heavy resources."""

    def __init__(self):
        self.transcriber = None
        self.love_analyzer = None
        self.sentence_reconstructor = None
        self.mix_player = None
        self.audio_processor = None
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
        love_threshold: float = 0.1,
        transcription_dir: str = "output_transcription",
        audio_dir: str = "audio",
    ):
        """Load all models. Called once at server startup."""
        logger.info("Loading models...")
        total_start = time.time()

        self._load_transcriber(whisper_model, whisper_language, whisper_device)
        self._load_love_analyzer(love_threshold)
        self._load_sentence_reconstructor()
        self._load_mix_player(transcription_dir, audio_dir)
        self._load_audio_processor()

        self._ready = True
        total_elapsed = time.time() - total_start
        logger.info("All models loaded in %.1fs", total_elapsed)
        for name, elapsed in self._load_times.items():
            logger.info("  %s: %.1fs", name, elapsed)

    def _load_transcriber(self, model_name: str, language: str, device: str):
        start = time.time()
        try:
            from src.transcriber_with_speakers import AudioTranscriberWithSpeakers

            device_arg = device if device else None
            self.transcriber = AudioTranscriberWithSpeakers(
                model_name=model_name,
                language=language,
                device=device_arg,
                enable_diarization=True,
                verbose=False,
            )
            logger.info(
                "Whisper '%s' loaded on %s",
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
                    device=device if device else None,
                    verbose=False,
                )
                logger.info("Loaded basic transcriber (no speaker diarization)")
            except Exception as e2:
                logger.error("Failed to load any transcriber: %s", e2)
        self._load_times["transcriber"] = time.time() - start

    def _load_love_analyzer(self, threshold: float):
        start = time.time()
        try:
            from src.love_analyzer import LoveTypeAnalyzer

            self.love_analyzer = LoveTypeAnalyzer(
                min_score_threshold=threshold,
                use_semantic_analysis=True,
                reconstruct_sentences=False,
            )
            logger.info("LoveTypeAnalyzer loaded")
        except Exception as e:
            logger.error("Failed to load love analyzer: %s", e)
        self._load_times["love_analyzer"] = time.time() - start

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

    def reload_mix_player_index(self):
        """Reload Mix-Play word index after new transcriptions are added."""
        if self.mix_player is not None:
            self.mix_player.load_transcriptions()
            word_count = len(self.mix_player.word_index) if hasattr(self.mix_player, "word_index") else 0
            logger.info("MixPlayer index reloaded, %d words indexed", word_count)


# Global singleton
models = ModelRegistry()
