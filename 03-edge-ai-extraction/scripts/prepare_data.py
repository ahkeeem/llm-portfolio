"""
Data preparation script for receipt fine-tuning.

Usage:
    python scripts/prepare_data.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_prep import convert_sroie_to_jsonl

if __name__ == "__main__":
    convert_sroie_to_jsonl()
