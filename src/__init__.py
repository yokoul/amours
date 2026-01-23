"""
Package de transcription audio avec timecodes précis.
"""

__version__ = "1.0.0"
__author__ = "Yan"
__description__ = "Extraction de mots et phrases avec timecodes de fichiers audio français"

from .transcriber import AudioTranscriber
from .audio_processor import AudioProcessor
from .export import ExportManager

__all__ = [
    "AudioTranscriber",
    "AudioProcessor", 
    "ExportManager"
]