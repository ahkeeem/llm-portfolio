#!/bin/bash

# Setup Dataset Subdirectories
mkdir -p datasets/compliance/raw
mkdir -p datasets/financial/raw
mkdir -p datasets/legal/raw
mkdir -p datasets/analytics/raw

# Read Kaggle Auth from .env
export KAGGLE_USERNAME=$(grep -i '^kaggle_username=' .env | cut -d '=' -f 2)
export KAGGLE_KEY=$(grep -i '^kaggle_token=' .env | cut -d '=' -f 2)

echo "Authenticating Kaggle as: $KAGGLE_USERNAME"

if ! command -v kaggle &> /dev/null
then
    echo "Kaggle CLI could not be found. Please run 'pip install kaggle'."
    exit 1
fi

echo "--- Fetching Compliance Dataset (Enron Email Subset) ---"
kaggle datasets download -d wcukierski/enron-email-dataset -p datasets/compliance/raw --unzip

echo "--- Fetching Financial Dataset (SEC 10-K) ---"
# Using a popular SEC 10K/10Q Kaggle dataset
kaggle datasets download -d finnhub/sec-filings -p datasets/financial/raw --unzip

echo "--- Fetching Analytics Dataset (Credit Card Transactions) ---"
kaggle datasets download -d mlg-ulb/creditcardfraud -p datasets/analytics/raw --unzip

# CUAD (Legal) is heavily hosted on HuggingFace, but Kaggle has a mirrored version
echo "--- Fetching Legal Dataset (CUAD) ---"
kaggle datasets download -d prajna20/cuad-v1 -p datasets/legal/raw --unzip

echo "✅ All datasets have been fetched to the /datasets/ directory."
