import os
import pandas as pd

def generate_samples():
    print("--- Starting Heavy Dataset Sampling (RAM Load Balanced) ---")

    # Target directory
    target_dir = "data/samples"
    os.makedirs(target_dir, exist_ok=True)

    # 1. Sample Enron Email Dataset
    email_raw = "datasets/compliance/raw/emails.csv"
    email_sample_path = os.path.join(target_dir, "emails_sample.csv")

    if os.path.exists(email_raw):
        print(f"Sampling Enron email corpus from: {email_raw}")
        # Load balanced reading: only read first chunk of 500 rows to limit memory
        for chunk in pd.read_csv(email_raw, chunksize=500):
            chunk.to_csv(email_sample_path, index=False)
            print(f"✅ Generated email sample at: {email_sample_path} (500 records)")
            break
    else:
        print(f"⚠️ Raw email dataset not found at {email_raw}. Skipping.")

    # 2. Sample Credit Card Dataset
    credit_raw = "datasets/analytics/raw/creditcard.csv"
    credit_sample_path = os.path.join(target_dir, "creditcard_sample.csv")

    if os.path.exists(credit_raw):
        print(f"Sampling credit card corpus from: {credit_raw}")
        # Load balanced reading: only read first chunk of 200 rows
        for chunk in pd.read_csv(credit_raw, chunksize=200):
            chunk.to_csv(credit_sample_path, index=False)
            print(f"✅ Generated credit card sample at: {credit_sample_path} (200 records)")
            break
    else:
        print(f"⚠️ Raw credit card dataset not found at {credit_raw}. Skipping.")

    # 3. Sample Financial Dataset
    fin_raw_dir = "datasets/financial/raw"
    fin_sample_path = os.path.join(target_dir, "financial_sample.csv")

    if os.path.exists(fin_raw_dir) and os.listdir(fin_raw_dir):
        # Pick the first available quarterly filing csv
        filing_files = sorted([f for f in os.listdir(fin_raw_dir) if f.endswith(".csv")])
        if filing_files:
            filing_file = filing_files[0]
            filing_path = os.path.join(fin_raw_dir, filing_file)
            print(f"Sampling financial corpus from: {filing_path}")
            for chunk in pd.read_csv(filing_path, chunksize=100):
                chunk.to_csv(fin_sample_path, index=False)
                print(f"✅ Generated financial filing sample at: {fin_sample_path} (100 records from {filing_file})")
                break
        else:
            print("⚠️ No quarterly filing CSVs found in financial raw directory.")
    else:
        print(f"⚠️ Raw financial dataset directory not found or empty at {fin_raw_dir}. Skipping.")

if __name__ == "__main__":
    generate_samples()
