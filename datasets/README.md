# Enterprise Datasets

This directory serves as the centralized injection point for data used across the Enterprise Agent Runtime (EAR).

To avoid bloated repositories and adhere to data privacy norms, large external datasets (like Kaggle or HuggingFace drops) are not committed to source control. Instead, each workflow expects data in specific formats located in these subdirectories.

## Current Setup

### `/compliance`
- **Source**: SROIE Dataset (HuggingFace)
- **Format**: `.txt` files containing OCR extracted text, paired with `.json` labels.
- **Action**: Place downloaded files into `/datasets/compliance/raw/`.

### `/financial`
- **Source**: SEC 10-K Filings / Financial Reports QA
- **Format**: `.json` or `.pdf`
- **Action**: Place downloaded files into `/datasets/financial/raw/`. 

### `/legal`
- **Source**: CUAD (Contract Understanding Atticus Dataset)
- **Format**: `.json` files containing contract text and annotated clauses.
- **Action**: Place downloaded files into `/datasets/legal/raw/`.

### `/analytics`
- **Source**: Spider Dataset
- **Format**: `.sqlite` and `tables.json`.
- **Action**: Place downloaded files into `/datasets/analytics/raw/`.

## Automated Setup (Future)
Future iterations will include `download_datasets.sh` inside `/scripts/` to programmatically fetch these via the Kaggle API and HuggingFace datasets library.
