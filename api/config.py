"""
Configuration for the Amours API server.

All settings are loaded from environment variables with sensible defaults
for local development.
"""

import os
from pathlib import Path


# Project root (parent of api/)
PROJECT_ROOT = Path(os.environ.get("AMOURS_PROJECT_ROOT", Path(__file__).parent.parent))

# Directories
AUDIO_DIR = Path(os.environ.get("AMOURS_AUDIO_DIR", PROJECT_ROOT / "audio"))
TRANSCRIPTION_DIR = Path(
    os.environ.get("AMOURS_TRANSCRIPTION_DIR", PROJECT_ROOT / "output_transcription")
)
SEMANTIC_DIR = Path(
    os.environ.get("AMOURS_SEMANTIC_DIR", PROJECT_ROOT / "output_semantic")
)
SENTENCES_DIR = Path(
    os.environ.get("AMOURS_SENTENCES_DIR", PROJECT_ROOT / "output_sentences")
)
MIX_PLAY_DIR = Path(
    os.environ.get("AMOURS_MIX_PLAY_DIR", PROJECT_ROOT / "output_mix_play")
)
GENERATED_AUDIO_DIR = Path(
    os.environ.get(
        "AMOURS_GENERATED_AUDIO_DIR", PROJECT_ROOT / "web-interface" / "public" / "audio"
    )
)
FRAMES_DIR = Path(
    os.environ.get(
        "AMOURS_FRAMES_DIR", PROJECT_ROOT / "web-interface" / "public" / "frames"
    )
)

# Upload settings
UPLOAD_DIR = Path(os.environ.get("AMOURS_UPLOAD_DIR", PROJECT_ROOT / "audio" / "uploads"))
MAX_UPLOAD_SIZE_MB = int(os.environ.get("AMOURS_MAX_UPLOAD_MB", "500"))

# Whisper model
WHISPER_MODEL = os.environ.get("AMOURS_WHISPER_MODEL", "medium")
WHISPER_LANGUAGE = os.environ.get("AMOURS_WHISPER_LANGUAGE", "fr")
WHISPER_DEVICE = os.environ.get("AMOURS_WHISPER_DEVICE", "")  # "" = auto-detect

# Love analyzer
LOVE_SCORE_THRESHOLD = float(os.environ.get("AMOURS_LOVE_THRESHOLD", "0.1"))

# Server
HOST = os.environ.get("AMOURS_HOST", "0.0.0.0")
PORT = int(os.environ.get("AMOURS_PORT", "8000"))
CORS_ORIGINS = os.environ.get("AMOURS_CORS_ORIGINS", "*").split(",")

# Workers (for uvicorn)
WORKERS = int(os.environ.get("AMOURS_WORKERS", "1"))


def ensure_directories():
    """Create all output directories if they don't exist."""
    for d in [
        AUDIO_DIR,
        TRANSCRIPTION_DIR,
        SEMANTIC_DIR,
        SENTENCES_DIR,
        MIX_PLAY_DIR,
        GENERATED_AUDIO_DIR,
        FRAMES_DIR,
        UPLOAD_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
