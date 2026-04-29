"""
Data preparation: Convert SROIE dataset to training format (JSONL).
"""

import json
import os


def convert_sroie_to_jsonl(
    raw_dir: str = "data/raw",
    train_output: str = "data/processed/train.jsonl",
    val_output: str = "data/processed/val.jsonl",
    val_split: float = 0.15,
):
    """
    Convert SROIE dataset files to instruction-tuning JSONL format.

    Each record becomes:
        {"input": "<receipt text>", "output": "<json fields>"}

    Args:
        raw_dir: Directory with SROIE data files.
        train_output: Path for training JSONL.
        val_output: Path for validation JSONL.
        val_split: Fraction of data for validation.
    """
    records = []

    # SROIE format: pairs of .txt (receipt text) and .json (labels)
    if os.path.exists(raw_dir):
        txt_files = [f for f in os.listdir(raw_dir) if f.endswith(".txt")]

        for txt_file in sorted(txt_files):
            json_file = txt_file.replace(".txt", ".json")
            txt_path = os.path.join(raw_dir, txt_file)
            json_path = os.path.join(raw_dir, json_file)

            if os.path.exists(json_path):
                with open(txt_path, "r") as f:
                    receipt_text = f.read().strip()
                with open(json_path, "r") as f:
                    labels = json.load(f)

                records.append({
                    "input": receipt_text,
                    "output": json.dumps(labels),
                })

    if not records:
        print("⚠️  No SROIE data found. Trying HuggingFace download...")
        records = _download_from_huggingface()

    if not records:
        print("❌ No data to process.")
        return

    # Split train/val
    split_idx = int(len(records) * (1 - val_split))
    train_records = records[:split_idx]
    val_records = records[split_idx:]

    # Save
    os.makedirs(os.path.dirname(train_output), exist_ok=True)
    _save_jsonl(train_records, train_output)
    _save_jsonl(val_records, val_output)

    print(f"✅ Train: {len(train_records)} records → {train_output}")
    print(f"✅ Val:   {len(val_records)} records → {val_output}")


def _download_from_huggingface() -> list[dict]:
    """Download SROIE data from HuggingFace."""
    try:
        from datasets import load_dataset

        dataset = load_dataset("darentang/sroie", split="train")

        records = []
        for item in dataset:
            receipt_text = item.get("text", item.get("words", ""))
            if isinstance(receipt_text, list):
                receipt_text = " ".join(receipt_text)

            labels = {
                "company": item.get("company", ""),
                "date": item.get("date", ""),
                "address": item.get("address", ""),
                "total": item.get("total", ""),
            }

            records.append({
                "input": receipt_text,
                "output": json.dumps(labels),
            })

        return records
    except ImportError:
        print("❌ Install datasets: pip install datasets")
        return []
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        return []


def _save_jsonl(records: list[dict], path: str):
    """Save records as JSONL."""
    with open(path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
