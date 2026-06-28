"""Shared test configuration.

Sets a safe, offline environment *before* the application settings are first
read, so no real LLM/network is ever required by the test suite.
"""
from __future__ import annotations

import os
import pathlib
import sys

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Use a throwaway DB and a placeholder key (never actually called — extraction
# is monkeypatched in the API tests).
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_skillbridge.db")
os.environ.setdefault("LLM_PROVIDER", "nvidia")
os.environ.setdefault("NVIDIA_API_KEY", "test-key-unused")
os.environ.setdefault("LOG_LEVEL", "WARNING")
