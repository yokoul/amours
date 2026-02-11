#!/usr/bin/env python3
"""
Launch the Amours API server.

Usage:
    python run_api.py
    python run_api.py --port 8000 --model large --device cuda

Environment variables (also configurable via CLI):
    AMOURS_PORT          Server port (default: 8000)
    AMOURS_WHISPER_MODEL Whisper model size (default: medium)
    AMOURS_WHISPER_DEVICE Device: cpu, cuda, or auto (default: auto)
"""

import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Amours API Server")
    parser.add_argument("--host", default=None, help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="Bind port (default: 8000)")
    parser.add_argument(
        "--model",
        default=None,
        help="Whisper model: tiny, base, small, medium, large (default: medium)",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Compute device: cpu, cuda, or empty for auto-detect",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    args = parser.parse_args()

    # CLI args override env vars
    if args.host:
        os.environ["AMOURS_HOST"] = args.host
    if args.port:
        os.environ["AMOURS_PORT"] = str(args.port)
    if args.model:
        os.environ["AMOURS_WHISPER_MODEL"] = args.model
    if args.device:
        os.environ["AMOURS_WHISPER_DEVICE"] = args.device

    # Import after env is set
    from api.config import HOST, PORT

    import uvicorn

    uvicorn.run(
        "api.app:app",
        host=HOST,
        port=PORT,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
