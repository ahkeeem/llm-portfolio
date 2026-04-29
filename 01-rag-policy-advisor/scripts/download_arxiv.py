"""
Download a subset of arXiv papers from HuggingFace datasets.

Usage:
    python scripts/download_arxiv.py

Prerequisites:
    pip install datasets
"""

import json
import os


def download_arxiv_subset(
    category: str = "cs.AI",
    max_papers: int = 100,
    output_dir: str = "data/raw",
):
    """
    Download arXiv paper abstracts from HuggingFace and save as text files.

    Args:
        category: arXiv category to filter (default: cs.AI)
        max_papers: Maximum number of papers to download
        output_dir: Directory to save the text files
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("❌ Install datasets: pip install datasets")
        return

    print(f"📥 Downloading arXiv papers (category: {category}, max: {max_papers})...")

    # Load arXiv dataset from HuggingFace
    dataset = load_dataset("ccdv/arxiv-classification", split="train", streaming=True)

    os.makedirs(output_dir, exist_ok=True)

    count = 0
    for item in dataset:
        if count >= max_papers:
            break

        text = item.get("text", "")
        if len(text) > 200:  # Skip very short entries
            filename = f"arxiv_{count:04d}.txt"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w") as f:
                f.write(text)
            count += 1

    print(f"✅ Downloaded {count} arXiv papers to {output_dir}/")


if __name__ == "__main__":
    download_arxiv_subset()
