# CLAUDE.md - AI Assistant Guide for Amours

## Project Overview

Amours is a French audio transcription and semantic analysis system that detects and classifies 7 types of love (romantique, familial, amical, spirituel, erotique, narcissique, platonique) in audio recordings. It combines Whisper AI transcription with sentence-transformer-based NLP to produce word-level timecoded transcriptions, speaker detection, and creative audio compositions (Mix-Play).

**Version:** 2.0.0
**Language:** Python 3.9+ (core + API), Node.js (legacy web interface)
**Author:** Yan

## Repository Structure

```
amours/
├── src/                        # Core Python library modules
│   ├── transcriber.py          # Whisper AI transcription engine
│   ├── transcriber_with_speakers.py  # Transcription + speaker diarization
│   ├── simple_transcriber_with_speakers.py  # Lightweight speaker detection
│   ├── love_analyzer.py        # 7-type love classification via embeddings
│   ├── sentence_reconstructor.py  # Syntax reconstruction from segments
│   ├── audio_processor.py      # Audio format conversion & normalization
│   ├── mix_player.py           # Audio composition engine (Mix-Play)
│   ├── video_processor.py      # Video demuxing, audio extraction, frame thumbnails (PyAV)
│   ├── export.py               # JSON/CSV export
│   ├── enriched_export.py      # Advanced export with metadata
│   ├── main.py                 # Basic CLI entry point
│   └── main_with_speakers.py   # CLI with speaker support
│
├── examples/                   # Example scripts, demos, and test scripts
│   ├── phrase_montage.py       # Phrase composition by keywords
│   ├── interactive_generator.py  # Interactive menu interface
│   ├── batch_generator.py      # Batch audio generation
│   ├── test_*.py               # Various test/demo scripts
│   └── ...                     # 25+ example files
│
├── web-interface/              # Node.js + Express web application
│   ├── server.js               # Main Express server
│   ├── poetic-server.js        # Poetic interface server (primary)
│   ├── public/                 # Static frontend (vanilla JS, p5.js)
│   └── python-bridge/          # Python-Node.js API bridge
│
├── api/                        # FastAPI server (persistent Python process)
│   ├── app.py                  # Main FastAPI application + all endpoints
│   ├── config.py               # Environment-based configuration
│   ├── models.py               # Singleton ML model registry (loaded once)
│   └── schemas.py              # Pydantic request/response models
│
├── run_api.py                  # API server entry point
│
├── gen/                        # Future voice generation features (stubs)
│
├── launcher_interactif.py      # Main interactive CLI launcher (recommended entry)
├── main_interactive.py         # Alternative interactive interface
├── final_mix_play.py           # Mix-Play comparative interface
├── transcribe_audio.py         # CLI transcription tool
├── analyze_love.py             # CLI love analysis tool
├── reconstruct_sentences.py    # Sentence reconstruction CLI
├── extract_vocabulary.py       # Word extraction tool
│
├── pyproject.toml              # Python project config (PEP 517)
├── requirements.txt            # Python dependencies
├── setup.sh                    # Full project setup script
├── launch.sh                   # Quick launch script
└── .gitignore                  # Excludes audio, outputs, JSON, CSV, SRT
```

### Output directories (gitignored, created at runtime)

- `audio/` - Input audio files
- `output_transcription/` - Transcription results
- `output_semantic/` - Love analysis results
- `output_sentences/` - Reconstructed sentences
- `output_mix_play/` - Generated audio compositions

## Development Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install runtime dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest black flake8 mypy
# Or: pip install -e ".[dev]"
```

Alternatively, run `./setup.sh` which automates venv creation, dependency installation, and output directory setup.

## Common Commands

```bash
# ── API server (recommended) ──
python run_api.py                          # Start API on port 8000
python run_api.py --port 8000 --model large --device cuda  # With options
# Then: curl http://localhost:8000/health

# ── CLI tools (still functional) ──
python launcher_interactif.py              # Interactive launcher
python transcribe_audio.py --input audio/file.mp3 --reconstruct-sentences
python analyze_love.py --input output_transcription/file_complete.json

# ── Legacy web interface ──
cd web-interface && node poetic-server.js  # Port 3000 (uses spawn)

# ── Development ──
black .          # Format code
flake8 .         # Lint
mypy src/ api/   # Type check
pytest           # Run tests
```

## Code Conventions

### Style

- **Formatter:** Black (line length 88, target Python 3.9)
- **Linter:** flake8
- **Type checker:** mypy
- All configured in `pyproject.toml`

### Naming

- Classes: `PascalCase` (e.g., `LoveAnalyzer`, `MixPlayer`)
- Functions/variables: `snake_case` (e.g., `analyze_love_types`, `semantic_score`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_THRESHOLD`)

### Docstrings

Google-style docstrings:

```python
def analyze_transcription(self, data: Dict, threshold: float = 0.15) -> Dict:
    """
    Analyse semantique d'une transcription pour detecter les types d'amour.

    Args:
        data: Donnees de transcription au format JSON
        threshold: Seuil de detection (0.0-1.0)

    Returns:
        Resultats d'analyse avec scores et classifications

    Raises:
        ValueError: Si les donnees sont invalides
    """
```

### Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: ajouter detection type d'amour spirituel
fix: corriger erreur parsing audio MP3
docs: mettre a jour guide d'installation
style: formater code avec Black
refactor: simplifier algorithme de clustering
test: ajouter tests pour sentence reconstructor
```

## Architecture Notes

### Core pipeline

1. **Audio/Video input** -> `audio_processor.py` / `video_processor.py` (format conversion, audio extraction from video)
2. **Transcription** -> `transcriber.py` / `transcriber_with_speakers.py` (Whisper AI, word-level timecodes)
3. **Frame extraction** (video only) -> `video_processor.py` (one thumbnail per transcription segment, PTS-based seeking)
4. **Sentence reconstruction** -> `sentence_reconstructor.py` (syntactic reassembly from Whisper segments)
5. **Semantic analysis** -> `love_analyzer.py` (sentence-transformers embeddings, cosine similarity against love-type reference phrases)
6. **Export** -> `export.py` / `enriched_export.py` (JSON, CSV, SRT)

### Video processing

`video_processor.py` handles video files transparently within the existing pipeline. When `/api/transcribe` receives a video file, the flow is:

1. **Detection**: `VideoProcessor.is_video()` checks for video streams via PyAV
2. **Audio extraction**: Demuxes audio to WAV mono 16kHz (Whisper-compatible)
3. **Transcription**: Standard Whisper pipeline runs on the extracted audio
4. **Frame extraction**: One thumbnail per transcription segment at the segment midpoint (PTS-based seeking)
5. **Response**: Includes `thumbnails` array with `image_url`, `segment_id`, `timestamp`, `width`, `height`

Frame images are served at `GET /frames/{video_stem}/{filename}`.

### Mix-Play system

`mix_player.py` builds a word index from transcription outputs and lets users compose new audio phrases by searching/selecting individual words across multiple speakers and source files. Features fuzzy matching, source diversification, and quality scoring.

### API server (`api/`)

FastAPI application (`run_api.py`) that loads all ML models once at startup and serves the full pipeline via REST. This replaces the Node.js `spawn()` pattern where each request launched a new Python process (reloading ~2 GB of models each time).

Key design: `api/models.py` holds a global `ModelRegistry` singleton. The `lifespan` handler in `app.py` calls `models.load_all()` once. All endpoints share the same in-memory models.

Endpoints: `POST /api/transcribe` (audio + video), `POST /api/analyze`, `POST /api/generate`, `GET /api/search`, `GET /api/search-sources`, `POST /api/extract-search-audio`, `POST /api/upload-contribution`, `GET /api/processing-status/{jobId}`, `GET /api/words`, `GET /api/random-words/{count}`, `GET /api/archive`, `POST /api/reload-index`, `GET /health`, `GET /frames/{path}` (video thumbnails).

Configuration via environment variables (see `api/config.py`) or CLI flags on `run_api.py`.

### Web interface (legacy)

Express server (`poetic-server.js`) on port 3000 with WebSocket (port 8080) for real-time updates. Frontend uses vanilla JS with p5.js for visualizations. The `python-bridge/api_wrapper.py` bridges Node.js requests to Python processing. Being replaced by the FastAPI server above.

### Key dependencies

| Dependency | Purpose |
|---|---|
| openai-whisper | Speech-to-text transcription |
| sentence-transformers | Semantic similarity embeddings |
| scikit-learn | ML classification |
| librosa | Audio feature extraction |
| pydub | Audio file manipulation |
| av (PyAV) | Video demuxing, audio/frame extraction (FFmpeg bindings) |
| pyannote.audio | Speaker diarization |
| torch | Deep learning backend |
| fastapi | REST API framework |
| uvicorn | ASGI server |

## File Patterns and Gitignore

The `.gitignore` excludes all audio files (`*.mp3`, `*.wav`, etc.), all JSON/CSV/SRT output files, and all `output*/` directories. When working with this project, be aware that:

- Audio and output files will not appear in git status
- Test scripts in `examples/` may require actual audio files in `audio/` to run
- The `tests/` directory referenced in CONTRIBUTING.md does not exist yet; test scripts live in `examples/`

## Testing

Tests are primarily integration-style scripts in `examples/` (e.g., `test_phrase.py`, `test_semantic_analysis.py`, `test_audio_quality.py`). Run with `pytest`. Many tests require audio data files that are not checked into the repository.

No dedicated `tests/` directory exists. When adding tests, place them in `examples/` following the existing `test_*.py` convention, or create a `tests/` directory if building a proper test suite.

## Important Considerations

- **Language:** The project documentation and UI are primarily in French. Code comments, variable names, and docstrings mix French and English.
- **Heavy dependencies:** Whisper, torch, and sentence-transformers are large. First-run downloads ML models (~1-3 GB).
- **Audio files:** Never commit audio files. They are gitignored.
- **Output files:** All JSON, CSV, and SRT files are gitignored. Do not commit generated outputs.
- **No CI/CD:** There are no GitHub Actions workflows. Testing is manual.
- **No Docker:** The project runs directly on the host system.
