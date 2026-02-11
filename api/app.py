"""
Amours API — FastAPI application.

Persistent Python process that loads ML models once at startup and
exposes the full Amours pipeline via REST endpoints.

All route names and response formats match the existing Express
(poetic-server.js) contract so the vanilla JS frontend works unchanged.
"""

import json
import logging
import os
import shutil
import sys
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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

# ── In-memory job store (contribution uploads) ────────────────

_jobs: Dict[str, Dict] = {}


# ── Lifecycle ──────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models at startup, release at shutdown."""
    config.ensure_directories()
    models.load_all(
        whisper_model=config.WHISPER_MODEL,
        whisper_language=config.WHISPER_LANGUAGE,
        whisper_device=config.WHISPER_DEVICE,
        whisper_backend=config.WHISPER_BACKEND,
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
            whisper_backend=models._whisper_backend,
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
        audio_path = opts.file_url
    else:
        raise HTTPException(400, "Provide either a file upload or file_url")

    extracted_audio = None  # Track temp WAV from video extraction
    video_source = None  # Track original video for frame extraction

    try:
        # ── Video detection: extract audio if input is a video ──
        is_video = False
        if models.video_processor is not None:
            try:
                from src.video_processor import VideoProcessor

                is_video = VideoProcessor.is_video(audio_path)
            except Exception:
                pass

        if is_video and models.video_processor is not None:
            logger.info("Video detected, extracting audio track...")
            video_source = audio_path
            extracted_audio = models.video_processor.extract_audio(audio_path)
            whisper_input = extracted_audio
        else:
            whisper_input = audio_path

        # ── Transcription ──
        transcriber = models.transcriber
        has_speakers = hasattr(transcriber, "transcribe_with_speakers")

        if opts.detect_speakers and has_speakers:
            result = transcriber.transcribe_with_speakers(
                whisper_input, word_timestamps=opts.word_timestamps
            )
        elif hasattr(transcriber, "transcribe_with_timestamps"):
            result = transcriber.transcribe_with_timestamps(
                whisper_input, word_timestamps=opts.word_timestamps
            )
        else:
            raise HTTPException(500, "No transcription method available")

        # Preserve original source filename in metadata
        if video_source:
            result.setdefault("metadata", {})["source_type"] = "video"
            result["metadata"]["video_path"] = video_source

        # ── Sentence reconstruction ──
        if opts.reconstruct_sentences and models.sentence_reconstructor:
            segments = result.get("transcription", {}).get("segments", [])
            if segments:
                reconstructed = models.sentence_reconstructor.reconstruct_sentences(
                    segments
                )
                result["transcription"]["original_segments"] = segments
                result["transcription"]["segments"] = reconstructed

        # ── Video frame extraction (aligned with transcription) ──
        thumbnails = []
        if video_source and models.video_processor is not None:
            segments = result.get("transcription", {}).get("segments", [])
            if segments:
                frames_dir = str(
                    config.FRAMES_DIR / Path(video_source).stem
                )
                try:
                    extractions = models.video_processor.extract_frames_for_segments(
                        video_source, segments, frames_dir
                    )
                    for ext in extractions:
                        # Build a URL-friendly path relative to FRAMES_DIR
                        rel_path = Path(ext.image_path).relative_to(
                            config.FRAMES_DIR
                        )
                        thumbnails.append(
                            {
                                "segment_id": ext.segment_id,
                                "timestamp": ext.timestamp,
                                "image_url": f"/frames/{rel_path}",
                                "image_path": ext.image_path,
                                "width": ext.width,
                                "height": ext.height,
                            }
                        )
                    result["thumbnails"] = thumbnails
                    logger.info("%d thumbnails extracted", len(thumbnails))
                except Exception as e:
                    logger.warning("Frame extraction failed: %s", e)

        # ── Love analysis ──
        love_data = None
        if opts.with_love_analysis and models.love_analyzer:
            enriched = models.love_analyzer.analyze_transcription(result)
            love_data = enriched.get("love_analysis")
            result["love_analysis"] = love_data

        _save_transcription(result, audio_path)
        models.reload_mix_player_index()

        metadata = result.get("metadata", {})
        transcription = result.get("transcription", {})

        response_data = {
            "success": True,
            "metadata": {
                "file": metadata.get("file", ""),
                "duration": metadata.get("duration", 0),
                "language": metadata.get("language"),
                "model": metadata.get("model"),
                "speakers_detected": metadata.get("speakers_detected"),
            },
            "text": transcription.get("text"),
            "segments": transcription.get("segments"),
            "love_analysis": love_data,
        }

        if video_source:
            response_data["metadata"]["source_type"] = "video"
            response_data["thumbnails"] = thumbnails

        return JSONResponse(response_data)

    except Exception as e:
        logger.exception("Transcription failed")
        return TranscribeResponse(success=False, error=str(e))

    finally:
        # Clean up temp files
        if file is not None and os.path.exists(audio_path):
            os.unlink(audio_path)
        if extracted_audio and os.path.exists(extracted_audio):
            os.unlink(extracted_audio)


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
    """Run semantic love type analysis on existing transcription data."""
    if models.love_analyzer is None:
        raise HTTPException(503, "Love analyzer model not loaded")

    try:
        if request.transcription_data:
            data = request.transcription_data
        elif request.transcription_file:
            file_path = config.TRANSCRIPTION_DIR / request.transcription_file
            if not file_path.suffix:
                file_path = file_path.with_suffix(".json")
            if not file_path.exists():
                raise HTTPException(
                    404, f"Transcription file not found: {file_path.name}"
                )
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise HTTPException(
                400, "Provide either transcription_file or transcription_data"
            )

        enriched = models.love_analyzer.analyze_transcription(data)
        love = enriched.get("love_analysis", {})

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
# Route: /api/generate (matches frontend fetch calls in poetic-interface.js)


@app.post("/api/generate")
async def generate(request: GenerateMixRequest):
    """
    Generate audio phrases using the Mix-Play system.

    Route name matches the existing Express endpoint that the
    poetic-interface.js frontend calls.
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

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            keywords_str = "_".join(request.words[:3])
            output_name = f"web_montage_{keywords_str}_{i}_{timestamp}.mp3"
            output_path = str(config.GENERATED_AUDIO_DIR / output_name)

            models.mix_player.generate_mixed_audio(
                composed_sentence=composed,
                output_path=output_path,
            )

            love_scores = None
            if models.love_analyzer:
                love_scores = models.love_analyzer.analyze_segment(composed.text)

            phrase_data = {
                "index": i,
                "text": composed.text,
                "speaker": (
                    composed.speakers_used[0] if composed.speakers_used else None
                ),
                "file_name": composed.files_used[0] if composed.files_used else None,
                "audio_path": (
                    composed.words[0].audio_path if composed.words else None
                ),
                "keywords_found": request.words,
                "match_score": 1.0,
                "start_time": composed.words[0].start if composed.words else 0,
                "end_time": composed.words[-1].end if composed.words else 0,
                "duration": composed.total_duration,
                "words": [
                    {"word": w.word, "start": w.start, "end": w.end}
                    for w in composed.words
                ],
                "love_type": (
                    max(love_scores, key=love_scores.get) if love_scores else None
                ),
                "love_analysis": love_scores,
            }
            phrases.append(phrase_data)
            audio_files.append(output_path)

        if not phrases:
            return JSONResponse(
                {"success": False, "error": f"Aucune phrase trouvee pour: {request.words}"}
            )

        total_duration = sum(p["duration"] for p in phrases)
        audio_url = f"/audio/{Path(audio_files[0]).name}" if audio_files else None

        # Aggregate semantic scores
        agg_scores = {}
        for p in phrases:
            if p.get("love_analysis"):
                for k, v in p["love_analysis"].items():
                    agg_scores[k] = agg_scores.get(k, 0) + v
        if agg_scores:
            n = len(phrases)
            agg_scores = {k: round(v / n, 4) for k, v in agg_scores.items()}

        return JSONResponse(
            {
                "success": True,
                "phrases": phrases,
                "audio_url": audio_url,
                "audioFile": audio_url,
                "duration_seconds": round(total_duration, 2),
                "keywords": request.words,
                "timestamp": int(time.time() * 1000),
                "semantic_analysis": agg_scores or None,
            }
        )

    except Exception as e:
        logger.exception("Mix-Play generation failed")
        return JSONResponse({"success": False, "error": str(e)})


# ── Generate single phrase audio ───────────────────────────────
# Route: /api/generate-phrase-audio/{phraseIndex}
# (poetic-interface.js calls this when user clicks download on a phrase)


@app.post("/api/generate-phrase-audio/{phrase_index}")
async def generate_phrase_audio(phrase_index: int, request: dict):
    """Generate audio for a single phrase on demand."""
    try:
        from pydub import AudioSegment

        phrase = request.get("phrase", {})
        audio_path = phrase.get("audio_path", "")
        start_time = phrase.get("start_time", 0)
        end_time = phrase.get("extended_end_time") or phrase.get("end_time", 0)

        if not audio_path or not Path(audio_path).exists():
            return JSONResponse({"success": False, "error": f"Fichier introuvable: {audio_path}"})

        audio = AudioSegment.from_file(audio_path)
        start_ms = max(0, int(start_time * 1000) - 100)
        end_ms = int(end_time * 1000) + 100
        segment = audio[start_ms:end_ms]

        segment = segment.fade_in(50).fade_out(50)

        keywords = phrase.get("keywords_found", ["extrait"])
        keyword_str = keywords[0].split("≈")[0] if keywords else "extrait"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"extrait_{keyword_str}_{phrase_index}_{timestamp}.mp3"
        output_path = config.GENERATED_AUDIO_DIR / output_name

        segment.export(str(output_path), format="mp3", bitrate="192k")

        return JSONResponse(
            {
                "success": True,
                "audio_file": output_name,
                "duration": round(len(segment) / 1000.0, 2),
                "phrase_index": phrase_index,
            }
        )

    except Exception as e:
        logger.exception("Phrase audio generation failed")
        return JSONResponse({"success": False, "error": str(e)})


# ── Search ─────────────────────────────────────────────────────
# Route: /api/search (matches search-module.js)


@app.get("/api/search")
async def search_transcriptions(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sources: Optional[str] = Query(None, description="Comma-separated source files"),
    context_duration: float = Query(60.0, description="Max context duration in seconds"),
):
    """Full-text search across all transcription files."""
    try:
        results = []
        source_filter = set()
        if sources:
            source_filter = {s.strip() for s in sources.split(",") if s.strip()}

        query_lower = q.lower()

        for json_file in sorted(config.TRANSCRIPTION_DIR.glob("*_complete.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            metadata = data.get("metadata", {})
            source_file = metadata.get("file", json_file.stem)
            source_path = metadata.get("path", "")

            if source_filter and source_file not in source_filter:
                continue

            segments = data.get("transcription", {}).get("segments", [])

            for seg in segments:
                seg_text = seg.get("text", "")
                seg_lower = seg_text.lower()

                if query_lower in seg_lower:
                    score = 1.0
                else:
                    ratio = SequenceMatcher(None, query_lower, seg_lower).ratio()
                    if ratio < 0.4:
                        continue
                    score = ratio

                seg_id = seg.get("id", 0)
                seg_start = seg.get("start", 0)

                # Build context segments (neighboring within context_duration)
                context_segments = []
                context_parts = []
                for ctx_seg in segments:
                    ctx_start = ctx_seg.get("start", 0)
                    if abs(ctx_start - seg_start) <= context_duration:
                        context_parts.append(ctx_seg.get("text", ""))
                        context_segments.append(
                            {
                                "id": ctx_seg.get("id", 0),
                                "text": ctx_seg.get("text", ""),
                                "start": ctx_seg.get("start", 0),
                                "end": ctx_seg.get("end", 0),
                                "speaker": ctx_seg.get("speaker"),
                                "words": ctx_seg.get("words"),
                            }
                        )

                results.append(
                    {
                        "source_file": source_file,
                        "source_path": source_path,
                        "transcription_file": json_file.stem,
                        "segment_id": seg_id,
                        "speaker": seg.get("speaker"),
                        "start_time": seg.get("start", 0),
                        "end_time": seg.get("end", 0),
                        "duration": seg.get(
                            "duration", seg.get("end", 0) - seg.get("start", 0)
                        ),
                        "matched_text": seg_text,
                        "context_text": " ".join(context_parts),
                        "context_segments": context_segments,
                        "relevance_score": round(score, 3),
                    }
                )

        results.sort(key=lambda r: r["relevance_score"], reverse=True)
        total = len(results)
        paginated = results[offset : offset + limit]

        return JSONResponse(
            {
                "success": True,
                "query": q,
                "total_results": total,
                "returned_results": len(paginated),
                "offset": offset,
                "limit": limit,
                "results": paginated,
            }
        )

    except Exception as e:
        logger.exception("Search failed")
        return JSONResponse({"success": False, "error": str(e)})


# ── Search sources ─────────────────────────────────────────────
# Route: /api/search-sources (matches search-module.js)


@app.get("/api/search-sources")
async def search_sources():
    """List available transcription source files for search filtering."""
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

    return JSONResponse({"success": True, "sources": sources, "count": len(sources)})


# ── Audio Extraction ───────────────────────────────────────────
# Route: /api/extract-search-audio (matches search-module.js)


@app.post("/api/extract-search-audio")
async def extract_search_audio(request: ExtractAudioRequest):
    """Extract a time segment from an audio file and return it as MP3."""
    try:
        from pydub import AudioSegment

        audio_path = Path(request.audio_path)
        if not audio_path.exists():
            return JSONResponse(
                {"success": False, "error": f"Fichier introuvable: {audio_path.name}"}
            )

        audio = AudioSegment.from_file(str(audio_path))
        start_ms = int(request.start_time * 1000)
        end_ms = int(request.end_time * 1000)
        segment = audio[start_ms:end_ms]

        segment = segment.fade_in(100).fade_out(100)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"search_{audio_path.stem}_{timestamp}.mp3"
        output_path = config.GENERATED_AUDIO_DIR / output_name

        segment.export(str(output_path), format="mp3", bitrate="192k")

        # Frontend expects "audio_file" (not "audio_url")
        return JSONResponse(
            {
                "success": True,
                "audio_file": output_name,
                "duration": round(len(segment) / 1000.0, 2),
                "size_bytes": output_path.stat().st_size,
            }
        )

    except Exception as e:
        logger.exception("Audio extraction failed")
        return JSONResponse({"success": False, "error": str(e)})


# ── Upload contribution ───────────────────────────────────────
# Route: /api/upload-contribution (matches audio-recorder.js)


@app.post("/api/upload-contribution")
async def upload_contribution(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    metadata: str = Form("{}"),
):
    """
    Upload user-recorded audio for transcription and analysis.

    Returns a jobId immediately; processing runs in the background.
    Poll /api/processing-status/{jobId} for progress.
    """
    job_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Parse metadata
    try:
        meta = json.loads(metadata)
    except json.JSONDecodeError:
        meta = {}

    # Save uploaded audio
    suffix = Path(audio.filename or "recording.webm").suffix or ".webm"
    audio_filename = f"contribution_{timestamp}_{job_id}{suffix}"
    contributions_dir = config.AUDIO_DIR / "contributions"
    contributions_dir.mkdir(parents=True, exist_ok=True)
    audio_path = contributions_dir / audio_filename

    content = await audio.read()
    with open(audio_path, "wb") as f:
        f.write(content)

    # Initialize job state
    _jobs[job_id] = {
        "jobId": job_id,
        "status": "processing",
        "progress": {"step": "upload", "message": "Fichier recu, demarrage..."},
        "audioFile": audio_filename,
        "startTime": time.time(),
    }

    # Process in background
    background_tasks.add_task(_process_contribution, job_id, str(audio_path), meta)

    return JSONResponse(
        {
            "success": True,
            "jobId": job_id,
            "message": "Contribution recue, traitement en cours...",
            "audioFile": audio_filename,
        }
    )


def _process_contribution(job_id: str, audio_path: str, meta: dict):
    """Background task: transcribe and analyze an uploaded contribution."""
    job = _jobs[job_id]

    try:
        # Step 1: Transcription
        job["progress"] = {"step": "transcription", "message": "Transcription en cours..."}

        if models.transcriber is None:
            raise RuntimeError("Transcriber not loaded")

        has_speakers = hasattr(models.transcriber, "transcribe_with_speakers")
        if has_speakers:
            result = models.transcriber.transcribe_with_speakers(
                audio_path, word_timestamps=True
            )
        else:
            result = models.transcriber.transcribe_with_timestamps(
                audio_path, word_timestamps=True
            )

        # Sentence reconstruction
        if models.sentence_reconstructor:
            segments = result.get("transcription", {}).get("segments", [])
            if segments:
                reconstructed = models.sentence_reconstructor.reconstruct_sentences(
                    segments
                )
                result["transcription"]["segments"] = reconstructed

        # Save transcription
        _save_transcription(result, audio_path)

        transcription = result.get("transcription", {})
        job["transcriptionText"] = transcription.get("text", "")
        job["words"] = []
        for seg in transcription.get("segments", []):
            for w in seg.get("words", []):
                job["words"].append(w)
        job["transcriptionFile"] = f"{Path(audio_path).stem}_complete.json"

        # Step 2: Semantic analysis
        job["progress"] = {
            "step": "semantic",
            "message": "Analyse semantique en cours...",
        }

        if models.love_analyzer:
            enriched = models.love_analyzer.analyze_transcription(result)
            love = enriched.get("love_analysis", {})
            stem = Path(audio_path).stem
            out_path = config.SEMANTIC_DIR / f"{stem}_love_analysis.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(enriched, f, ensure_ascii=False, indent=2)
            job["semanticFile"] = out_path.name
            job["semanticAnalysis"] = love

        # Done
        models.reload_mix_player_index()
        job["status"] = "completed"
        job["progress"] = {"step": "done", "message": "Traitement termine"}
        job["processingDuration"] = round(time.time() - job["startTime"], 1)

    except Exception as e:
        logger.exception("Contribution processing failed for job %s", job_id)
        job["status"] = "error"
        job["error"] = str(e)
        job["progress"] = {"step": "error", "message": str(e)}


# ── Processing status ─────────────────────────────────────────
# Route: /api/processing-status/{jobId} (matches recording-interface.js)


@app.get("/api/processing-status/{job_id}")
async def processing_status(job_id: str):
    """Check the processing status of an uploaded contribution."""
    job = _jobs.get(job_id)
    if job is None:
        return JSONResponse(
            {"jobId": job_id, "status": "unknown", "error": "Job non trouve"},
            status_code=404,
        )
    return JSONResponse(job)


# ── Words ──────────────────────────────────────────────────────
# Route: /api/words (matches poetic-interface.js)
# The frontend expects a plain JSON array of strings.


@app.get("/api/words")
async def get_words():
    """Return a list of inspirational French words about love."""
    words = [
        "amour", "tendresse", "passion", "desir",
        "coeur", "caresse", "emotion", "reve",
        "douceur", "bonheur", "partage", "confiance",
        "espoir", "lumiere", "intimite", "eternite",
    ]
    return JSONResponse(words)


# ── Random words from index ───────────────────────────────────
# Route: /api/random-words/{count} (matches app.js spectacle interface)


@app.get("/api/random-words/{count}")
async def get_random_words(count: int):
    """Get N random words from the Mix-Play word index."""
    import random

    if models.mix_player is None or not hasattr(models.mix_player, "word_index"):
        return JSONResponse([])

    all_words = list(models.mix_player.word_index.keys())
    sample = random.sample(all_words, min(count, len(all_words)))
    return JSONResponse(sample)


# ── Archive ────────────────────────────────────────────────────
# Route: /api/archive (matches poetic-server.js archive endpoint)


@app.get("/api/archive")
async def get_archive():
    """Return recent generated audio creations."""
    creations = []

    for audio_file in sorted(
        config.GENERATED_AUDIO_DIR.glob("web_montage_*.mp3"), reverse=True
    ):
        if len(creations) >= 20:
            break
        stat = audio_file.stat()
        creations.append(
            {
                "filename": audio_file.name,
                "audio_url": f"/audio/{audio_file.name}",
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size_bytes": stat.st_size,
            }
        )

    return JSONResponse({"success": True, "creations": creations, "count": len(creations)})


# ── Reload index ───────────────────────────────────────────────


@app.post("/api/reload-index")
async def reload_index():
    """Reload Mix-Play word index after transcription files change."""
    models.reload_mix_player_index()
    word_count = 0
    if models.mix_player and hasattr(models.mix_player, "word_index"):
        word_count = len(models.mix_player.word_index)
    return JSONResponse({"success": True, "words_indexed": word_count})


# ── Audio serving ──────────────────────────────────────────────
# Serves from generated audio dir AND output_mix_play/ (like Express did)


@app.get("/audio/{filename:path}")
async def serve_audio(filename: str):
    """Serve generated audio files."""
    for directory in [config.GENERATED_AUDIO_DIR, config.MIX_PLAY_DIR]:
        file_path = directory / filename
        if file_path.exists() and file_path.is_file():
            return FileResponse(
                str(file_path),
                media_type="audio/mpeg",
                headers={"Accept-Ranges": "bytes"},
            )

    raise HTTPException(404, f"Audio file not found: {filename}")


# ── Audio source files ─────────────────────────────────────────
# Serves original audio sources (like Express: /audio-sources → audio/)


@app.get("/audio-sources/{filename:path}")
async def serve_audio_source(filename: str):
    """Serve original audio source files."""
    file_path = config.AUDIO_DIR / filename
    if file_path.exists() and file_path.is_file():
        suffix = file_path.suffix.lower()
        media_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
            ".flac": "audio/flac",
            ".webm": "audio/webm",
        }
        return FileResponse(
            str(file_path),
            media_type=media_types.get(suffix, "application/octet-stream"),
            headers={"Accept-Ranges": "bytes"},
        )

    raise HTTPException(404, f"Audio source not found: {filename}")


# ── Video frame thumbnails ────────────────────────────────────
# Serves extracted frame images from video transcription


@app.get("/frames/{filename:path}")
async def serve_frame(filename: str):
    """Serve extracted video frame thumbnails."""
    file_path = config.FRAMES_DIR / filename
    if file_path.exists() and file_path.is_file():
        suffix = file_path.suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        return FileResponse(
            str(file_path),
            media_type=media_types.get(suffix, "image/jpeg"),
        )

    raise HTTPException(404, f"Frame not found: {filename}")


# ── Static frontend (mounted last so API routes take priority) ─
# Serves web-interface/public/ at root, including poetic-interface.html


STATIC_DIR = PROJECT_ROOT / "web-interface" / "public"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
