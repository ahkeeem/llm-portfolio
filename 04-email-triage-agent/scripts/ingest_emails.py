"""
Ingestion script for Enron Email Dataset.

Downloads and preprocesses email data from Kaggle into a clean JSONL format.

Usage:
    python scripts/ingest_emails.py

Prerequisites:
    pip install kaggle pandas
    Set KAGGLE_USERNAME and KAGGLE_KEY in your environment.
"""

import json
import os

import pandas as pd


def load_enron_data(raw_path: str = "data/raw/emails.csv") -> pd.DataFrame:
    """Load the raw Enron email CSV."""
    if not os.path.exists(raw_path):
        print(f"❌ Raw data not found at {raw_path}")
        print("Download from: https://www.kaggle.com/datasets/wcukierski/enron-email-dataset")
        print(f"Place the CSV at: {raw_path}")
        return pd.DataFrame()

    df = pd.read_csv(raw_path)
    print(f"✅ Loaded {len(df)} emails from {raw_path}")
    return df


def extract_body(message: str) -> str:
    """Extract the email body from a raw email message string."""
    if not isinstance(message, str):
        return ""
    # Split on first blank line (after headers)
    parts = message.split("\n\n", 1)
    return parts[1].strip() if len(parts) > 1 else message.strip()


def preprocess(df: pd.DataFrame, max_samples: int = 500) -> list[dict]:
    """Clean and sample emails for the agent pipeline."""
    if df.empty:
        return []

    df = df.dropna(subset=["message"])
    df = df.head(max_samples)

    records = []
    for _, row in df.iterrows():
        body = extract_body(row["message"])
        if len(body) > 50:  # Skip very short emails
            records.append({"email_text": body})

    return records


def save_processed(records: list[dict], output_path: str = "data/processed/emails.jsonl"):
    """Save processed emails as JSONL."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    print(f"✅ Saved {len(records)} processed emails to {output_path}")


if __name__ == "__main__":
    df = load_enron_data()
    records = preprocess(df)
    if records:
        save_processed(records)
