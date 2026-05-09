import urllib.request
import os
import zipfile

url = "https://zenodo.org/record/4595826/files/CUAD_v1.zip?download=1"
dest_path = "datasets/legal/raw/CUAD_v1.zip"

print("Downloading CUAD dataset from Zenodo...")
urllib.request.urlretrieve(url, dest_path)
print("Downloaded CUAD_v1.zip successfully.")

print("Extracting...")
with zipfile.ZipFile(dest_path, 'r') as zip_ref:
    zip_ref.extractall("datasets/legal/raw/")
print("Extraction complete.")
