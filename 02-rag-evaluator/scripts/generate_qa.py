"""
Script to generate QA pairs for RAG evaluation.

Usage:
    python scripts/generate_qa.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.qa_generator import generate_qa_dataset

if __name__ == "__main__":
    generate_qa_dataset()
