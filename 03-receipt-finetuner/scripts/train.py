"""
Training script for LoRA fine-tuning.

Usage:
    python scripts/train.py

Requires GPU with >= 16GB VRAM for 4-bit quantized training.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.trainer import train

if __name__ == "__main__":
    train_path = "data/processed/train.jsonl"
    val_path = "data/processed/val.jsonl"

    if not os.path.exists(train_path):
        print(f"❌ Training data not found at {train_path}")
        print("Run: python scripts/prepare_data.py first")
        exit(1)

    train(train_path, val_path)
