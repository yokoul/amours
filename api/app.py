"""
Amours API — FastAPI application.

Persistent Python process that loads ML models once at startup and
exposes the full Amours pipeline via REST endpoints.
"""

import json
import logging
import os
import sys
import tempfile
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Ensure project root is on sys.path so `from src.xxx import` works
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api import config
from api.models import models
from api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ExtractAudioRequest,
    ExtractAudioResponse,
    GenerateMixRequest,
    GenerateMixResponse,
    HealthResponse,
    ModelsStatus,
    PhraseData,
    SearchResponse,
    SearchResult,
    TranscribeRequest,
    TranscribeResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("amours.api")


# ── Lifecycle ──────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models at startup, release at shutdown."""
    config.ensure_directories()
    models.load_all(
        whisper_model=config.WHISPER_MODEL,
        whisper_language=config.WHISPER_LANGUAGE,
        whisper_device=config.WHISPER_DEVICE,
        love_threshold=config.LOVE_SCORE_THRESHOLD,
        transcription_dir=str(config.TRANSCRIPTION_DIR),
        audio_dir=str(config.AUDIO_DIR),
    )
    yield
    logger.info("Shutting down Amours API")


app = FastAPI(
    title="Amours API",
    description="Audio transcription and semantic love analysis",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ─────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse)
async def health():
    """Check API status and model availability."""
    mix_words = 0
    if models.mix_player and hasattr(models.mix_player, "word_index"):
        mix_words = len(models.mix_player.word_index)

    return HealthResponse(
        status="ready" if models.ready else "loading",
        version="2.0.0",
        models=ModelsStatus(
            whisper=models.transcriber is not None,
            whisper_model=config.WHISPER_MODEL,
            love_analyzer=models.love_analyzer is not None,
            mix_player=models.mix_player is not None,
            mix_player_words_indexed=mix_words,
        ),
    )


# ── Transcription ─────────────────────────────────────────────


@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: Optional[UploadFile] = File(None),
    options: Optional[str] = None,
):
    """
    Transcribe an audio or video file.

    Send the file as multipart upload. Optionally pass a JSON string
    in the `options` form field with TranscribeRequest fields.
    """
    if models.transcriber is None:
        raise HTTPException(503, "Transcriber model not loaded")

    # Parse options
    opts = TranscribeRequest()
    if options:
        opts = TranscribeRequest.model_validate_json(options)

    # Determine input file
    if file is not None:
        suffix = Path(file.filename or "upload").suffix or ".mp3"
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, dir=str(config.UPLOAD_DIR)
        )
        try:
            content = await file.read()
            tmp.write(content)
            tmp.flush()
            audio_path = tmp.name
        finally:
            tmp.close()
    elif opts.file_url:
        # Remote URL — let PyAV/ffmpeg handle it directly if possible,
        # otherwise download to temp file
        audio_path = opts.file_url
    else:
        raise HTTPException(400, "Provide either a file upload or file_url")

    try:
        # Choose transcription method based on available transcriber
        transcriber = models.transcriber
        has_speakers = hasattr(transcriber, "transcribe_with_speakers")

        if opts.detect_speakers and has_speakers:
            result = transcriber.transcribe_with_speakers(
                audio_path, word_timestamps=opts.word_timestamps
            )
        elif hasattr(transcriber, "transcribe_with_timestamps"):
            result = transcriber.transcribe_with_timestamps(
                audio_path, word_timestamps=opts.word_timestamps
            )
        else:
            raise HTTPException(500, "No transcription method available")

        # Sentence reconstruction
        if opts.reconstruct_sentences and models.sentence_reconstructor:
            segments = result.get("transcription", {}).get("segments", [])
            if segments:
                reconstructed = models.sentence_reconstructor.reconstruct_sentences(
                    segments
                )
                result["transcription"]["original_segments"] = segments
                result["transcription"]["segments"] = reconstructed

        # Love analysis
        love_data = None
        if opts.with_love_analysis and models.love_analyzer:
            enriched = models.love_analyzer.analyze_transcription(result)
            love_data = enriched.get("love_analysis")
            result["love_analysis"] = love_data

        # Save transcription to output directory
        _save_transcription(result, audio_path)

        # Reload mix player index so new words are available
        models.reload_mix_player_index()

        metadata = result.get("metadata", {})
        transcription = result.get("transcription", {})

        return TranscribeResponse(
            success=True,
            metadata={
                "file": metadata.get("file", ""),
                "duration": metadata.get("duration", 0),
                "language": metadata.get("language"),
                "model": metadata.get("model"),
                "speakers_detected": metadata.get("speakers_detected"),
            },
            text=transcription.get("text"),
            segments=transcription.get("segments"),
            love_analysis=love_data,
        )

    except Exception as e:
        logger.exception("Transcription failed")
        return TranscribeResponse(success=False, error=str(e))

    finally:
        # Clean up uploaded temp file
        if file is not None and os.path.exists(audio_path):
            os.unlink(audio_path)


def _save_transcription(result: Dict, audio_path: str):
    """Save transcription result to the output directory."""
    filename = Path(audio_path).stem
    output_path = config.TRANSCRIPTION_DIR / f"{filename}_complete.json"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info("Transcription saved to %s", output_path)
    except Exception as e:
        logger.warning("Could not save transcription: %s", e)


# ── Love Analysis ──────────────────────────────────────────────


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_love(request: AnalyzeRequest):
    """
    Run semantic love type analysis on existing transcription data.

    Provide either a transcription_file name (looked up in output_transcription/)
    or inline transcription_data.
    """
    if models.love_analyzer is None:
        raise HTTPException(503, "Love analyzer model not loaded")

    try:
        # Load transcription data
        if request.transcription_data:
            data = request.transcription_data
        elif request.transcription_file:
            file_path = config.TRANSCRIPTION_DIR / request.transcription_file
            if not file_path.suffix:
                file_path = file_path.with_suffix(".json")
            if not file_path.exists():
                raise HTTPException(404, f"Transcription file not found: {file_path.name}")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise HTTPException(
                400, "Provide either transcription_file or transcription_data"
            )

        # Run analysis
        enriched = models.love_analyzer.analyze_transcription(data)
        love = enriched.get("love_analysis", {})

        # Save enriched output
        if request.transcription_file:
            stem = Path(request.transcription_file).stem
            out_path = config.SEMANTIC_DIR / f"{stem}_love_analysis.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(enriched, f, ensure_ascii=False, indent=2)

        stats = love.get("statistics_by_type", {})
        return AnalyzeResponse(
            success=True,
            statistics_by_type=stats,
            segments_with_love_content=love.get("segments_with_love_content"),
            total_segments=love.get("total_segments"),
            enriched_data=enriched,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Love analysis failed")
        return AnalyzeResponse(success=False, error=str(e))


# ── Mix-Play Generation ────────────────────────────────────────


@app.post("/api/generate-mix", response_model=GenerateMixResponse)
async def generate_mix(request: GenerateMixRequest):
    """
    Generate audio phrases using the Mix-Play system.

    Searches the word index for matching keywords and composes
    audio montages from different speakers and source files.
    """
    if models.mix_player is None:
        raise HTTPException(503, "MixPlayer not loaded (no transcriptions available?)")

    try:
        phrases = []
        audio_files = []

        for i in range(request.count):
            composed = models.mix_player.compose_sentence(
                words=request.words,
                prioritize_diversity=True,
            )
            if composed is None:
                continue

            # Generate audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            keywords_str = "_".join(request.words[:3])
            output_name = f"web_montage_{keywords_str}_{i}_{timestamp}.mp3"
            output_path = str(config.GENERATED_AUDIO_DIR / output_name)

            models.mix_player.generate_mixed_audio(
                composed_sentence=composed,
                output_path=output_path,
            )

            # Love analysis on composed text if available
            love_scores = None
            if models.love_analyzer:
                love_scores = models.love_analyzer.analyze_segment(composed.text)

            phrases.append(
                PhraseData(
                    index=i,
                    text=composed.text,
                    speaker=composed.speakers_used[0] if composed.speakers_used else None,
                    file_name=composed.files_used[0] if composed.files_used else None,
                    start_time=composed.words[0].start if composed.words else 0,
                    end_time=composed.words[-1].end if composed.words else 0,
                    duration=composed.total_duration,
                    keywords_found=request.words,
                    love_type=max(love_scores, key=love_scores.get) if love_scores else None,
                    love_analysis=love_scores,
                )
            )
            audio_files.append(output_path)

        if not phrases:
            return GenerateMixResponse(
                success=False,
                error=f"No phrases found for keywords: {request.words}",
            )

        # Combine all audio files into one montage
        total_duration = sum(p.duration for p in phrases)
        audio_url = f"/audio/{Path(audio_files[0]).name}" if audio_files else None

        # Aggregate semantic scores
        agg_scores = {}
        for p in phrases:
            if p.love_analysis:
                for k, v in p.love_analysis.items():
                    agg_scores[k] = agg_scores.get(k, 0) + v
        if agg_scores:
            n = len(phrases)
            agg_scores = {k: round(v / n, 4) for k, v in agg_scores.items()}

        return GenerateMixResponse(
            success=True,
            phrases=phrases,
            audio_url=audio_url,
            duration_seconds=round(total_duration, 2),
            keywords=request.words,
            semantic_analysis=agg_scores or None,
        )

    except Exception as e:
        logger.exception("Mix-Play generation failed")
        return GenerateMixResponse(success=False, error=str(e))


# ── Search ─────────────────────────────────────────────────────


@app.get("/api/search", response_model=SearchResponse)
async def search_transcriptions(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sources: Optional[str] = Query(None, description="Comma-separated source files"),
    context_duration: float = Query(60.0, description="Max context duration in seconds"),
):
    """
    Full-text search across all transcription files.

    Returns matching segments with context and pagination.
    """
    try:
        results = []
        source_filter = set()
        if sources:
            source_filter = {s.strip() for s in sources.split(",") if s.strip()}

        query_lower = q.lower()

        # Search through transcription JSON files
        for json_file in sorted(config.TRANSCRIPTION_DIR.glob("*_complete.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            metadata = data.get("metadata", {})
            source_file = metadata.get("file", json_file.stem)

            if source_filter and source_file not in source_filter:
                continue

            segments = data.get("transcription", {}).get("segments", [])
            source_path = metadata.get("path", "")

            for seg in segments:
                seg_text = seg.get("text", "")
                seg_lower = seg_text.lower()

                # Exact substring match or fuzzy match
                if query_lower in seg_lower:
                    score = 1.0
                else:
                    ratio = SequenceMatcher(None, query_lower, seg_lower).ratio()
                    if ratio < 0.4:
                        continue
                    score = ratio

                # Build context from neighboring segments
                seg_id = seg.get("id", 0)
                context_parts = []
                for ctx_seg in segments:
                    ctx_start = ctx_seg.get("start", 0)
                    seg_start = seg.get("start", 0)
                    if abs(ctx_start - seg_start) <= context_duration:
                        context_parts.append(ctx_seg.get("text", ""))

                results.append(
                    SearchResult(
                        source_file=source_file,
                        segment_id=seg_id,
                        speaker=seg.get("speaker"),
                        start_time=seg.get("start", 0),
                        end_time=seg.get("end", 0),
                        duration=seg.get("duration", seg.get("end", 0) - seg.get("start", 0)),
                        matched_text=seg_text,
                        context_text=" ".join(context_parts) if context_parts else None,
                        relevance_score=round(score, 3),
                    )
                )

        # Sort by relevance
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        total = len(results)
        paginated = results[offset : offset + limit]

        return SearchResponse(
            success=True,
            query=q,
            total_results=total,
            returned_results=len(paginated),
            offset=offset,
            limit=limit,
            results=paginated,
        )

    except Exception as e:
        logger.exception("Search failed")
        return SearchResponse(success=False, error=str(e))


# ── Audio Extraction ───────────────────────────────────────────


@app.post("/api/extract-audio", response_model=ExtractAudioResponse)
async def extract_audio(request: ExtractAudioRequest):
    """Extract a time segment from an audio file and return it as MP3."""
    try:
        from pydub import AudioSegment

        audio_path = Path(request.audio_path)
        if not audio_path.exists():
            raise HTTPException(404, f"Audio file not found: {audio_path.name}")

        audio = AudioSegment.from_file(str(audio_path))
        start_ms = int(request.start_time * 1000)
        end_ms = int(request.end_time * 1000)
        segment = audio[start_ms:end_ms]

        # Apply fade in/out
        segment = segment.fade_in(100).fade_out(100)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"extract_{audio_path.stem}_{timestamp}.mp3"
        output_path = config.GENERATED_AUDIO_DIR / output_name

        segment.export(str(output_path), format="mp3", bitrate="192k")

        return ExtractAudioResponse(
            success=True,
            audio_url=f"/audio/{output_name}",
            duration=round(len(segment) / 1000.0, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Audio extraction failed")
        return ExtractAudioResponse(success=False, error=str(e))


# ── Static audio serving ──────────────────────────────────────


@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated audio files."""
    # Check multiple directories
    for directory in [config.GENERATED_AUDIO_DIR, config.MIX_PLAY_DIR]:
        file_path = directory / filename
        if file_path.exists():
            return FileResponse(
                str(file_path),
                media_type="audio/mpeg",
                headers={"Accept-Ranges": "bytes"},
            )

    raise HTTPException(404, f"Audio file not found: {filename}")


# ── Utility endpoints ─────────────────────────────────────────


@app.post("/api/reload-index")
async def reload_index():
    """Reload Mix-Play word index after transcription files change."""
    models.reload_mix_player_index()
    word_count = 0
    if models.mix_player and hasattr(models.mix_player, "word_index"):
        word_count = len(models.mix_player.word_index)
    return {"success": True, "words_indexed": word_count}


@app.get("/api/sources")
async def list_sources():
    """List available transcription source files."""
    sources = []
    for json_file in sorted(config.TRANSCRIPTION_DIR.glob("*_complete.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            metadata = data.get("metadata", {})
            sources.append(
                {
                    "file": metadata.get("file", json_file.stem),
                    "duration": metadata.get("duration"),
                    "speakers_detected": metadata.get("speakers_detected"),
                    "transcription_file": json_file.name,
                }
            )
        except (json.JSONDecodeError, OSError):
            continue

    return {"success": True, "sources": sources, "count": len(sources)}


@app.get("/api/words")
async def get_words(count: int = Query(10, ge=1, le=100)):
    """Get random words from the Mix-Play word index."""
    if models.mix_player is None or not hasattr(models.mix_player, "word_index"):
        return {"success": True, "words": [], "count": 0}

    import random

    all_words = list(models.mix_player.word_index.keys())
    sample = random.sample(all_words, min(count, len(all_words)))
    return {"success": True, "words": sample, "count": len(sample)}
