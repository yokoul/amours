"""
Pydantic models for API request/response validation.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


# ── Transcription ──────────────────────────────────────────────


class TranscribeRequest(BaseModel):
    """Request body for transcription endpoint."""

    file_url: Optional[str] = Field(
        None, description="URL of remote audio/video file to transcribe"
    )
    model: Optional[str] = Field(None, description="Whisper model override")
    language: Optional[str] = Field(None, description="Language override (e.g. 'fr')")
    word_timestamps: bool = Field(True, description="Enable word-level timecodes")
    detect_speakers: bool = Field(True, description="Enable speaker diarization")
    reconstruct_sentences: bool = Field(
        True, description="Enable sentence reconstruction"
    )
    with_love_analysis: bool = Field(
        False, description="Run love type analysis after transcription"
    )


class WordData(BaseModel):
    word: str
    start: float
    end: float
    duration: float
    confidence: Optional[float] = None
    speaker: Optional[str] = None


class SegmentData(BaseModel):
    id: int
    start: float
    end: float
    duration: float
    text: str
    speaker: Optional[str] = None
    words: Optional[List[WordData]] = None
    love_analysis: Optional[Dict[str, float]] = None
    dominant_love_type: Optional[str] = None


class TranscriptionMetadata(BaseModel):
    file: str
    duration: float
    language: Optional[str] = None
    model: Optional[str] = None
    speakers_detected: Optional[int] = None


class TranscribeResponse(BaseModel):
    success: bool
    metadata: Optional[TranscriptionMetadata] = None
    text: Optional[str] = None
    segments: Optional[List[SegmentData]] = None
    love_analysis: Optional[Dict] = None
    error: Optional[str] = None


# ── Love Analysis ──────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Request body for semantic love analysis."""

    transcription_file: Optional[str] = Field(
        None,
        description="Filename of transcription in output_transcription/ to analyze",
    )
    transcription_data: Optional[Dict] = Field(
        None, description="Inline transcription data to analyze"
    )
    threshold: float = Field(0.1, description="Minimum score threshold")


class LoveTypeStats(BaseModel):
    average_score: float
    max_score: float
    segments_count: int


class AnalyzeResponse(BaseModel):
    success: bool
    statistics_by_type: Optional[Dict[str, LoveTypeStats]] = None
    segments_with_love_content: Optional[int] = None
    total_segments: Optional[int] = None
    enriched_data: Optional[Dict] = None
    error: Optional[str] = None


# ── Mix-Play Generation ────────────────────────────────────────


class GenerateMixRequest(BaseModel):
    """Request body for Mix-Play phrase generation."""

    words: List[str] = Field(..., description="Keywords to search for")
    count: int = Field(3, description="Number of phrases to generate", ge=1, le=20)
    include_next: int = Field(
        0, description="Include N following phrases from same speaker"
    )


class PhraseData(BaseModel):
    index: int
    text: str
    speaker: Optional[str] = None
    file_name: Optional[str] = None
    start_time: float
    end_time: float
    duration: float
    keywords_found: Optional[List[str]] = None
    love_type: Optional[str] = None
    love_analysis: Optional[Dict[str, float]] = None


class GenerateMixResponse(BaseModel):
    success: bool
    phrases: Optional[List[PhraseData]] = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    keywords: Optional[List[str]] = None
    semantic_analysis: Optional[Dict[str, float]] = None
    error: Optional[str] = None


# ── Search ─────────────────────────────────────────────────────


class SearchResult(BaseModel):
    source_file: str
    segment_id: int
    speaker: Optional[str] = None
    start_time: float
    end_time: float
    duration: float
    matched_text: str
    context_text: Optional[str] = None
    relevance_score: float


class SearchResponse(BaseModel):
    success: bool
    query: Optional[str] = None
    total_results: int = 0
    returned_results: int = 0
    offset: int = 0
    limit: int = 10
    results: Optional[List[SearchResult]] = None
    error: Optional[str] = None


# ── Audio Extraction ───────────────────────────────────────────


class ExtractAudioRequest(BaseModel):
    """Request body for audio segment extraction."""

    audio_path: str = Field(..., description="Path to source audio file")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")


class ExtractAudioResponse(BaseModel):
    success: bool
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None


# ── Health ─────────────────────────────────────────────────────


class ModelsStatus(BaseModel):
    whisper: bool = False
    whisper_model: Optional[str] = None
    love_analyzer: bool = False
    mix_player: bool = False
    mix_player_words_indexed: int = 0


class HealthResponse(BaseModel):
    status: str
    version: str
    models: ModelsStatus
