#!/usr/bin/env python3
"""Launcher script for NIDS SOC Dashboard Server."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import uvicorn
from dashboard.backend.config import HOST, PORT


def parse_args():
    parser = argparse.ArgumentParser(description="Start NIDS Enterprise SOC Dashboard Server.")
    parser.add_argument("--host", type=str, default=HOST, help=f"Host address (default: {HOST})")
    parser.add_argument("--port", type=int, default=PORT, help=f"Port number (default: {PORT})")
    parser.add_argument("--reload", action="store_true", help="Enable code hot-reload")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"\n🚀 Starting NIDS SOC Command Dashboard on http://{args.host}:{args.port}")
    print(f"📖 Interactive API Docs: http://{args.host}:{args.port}/docs\n")
    uvicorn.run("dashboard.backend.server:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
