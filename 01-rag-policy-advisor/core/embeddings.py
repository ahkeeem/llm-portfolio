import os
from chromadb.utils import embedding_functions

# Patch ChromaDB's hardcoded cache path to be inside the workspace
import chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 as onnx_module
import pathlib
workspace_cache = pathlib.Path(__file__).parent.parent.parent / ".chroma_cache" / "onnx_models" / "all-MiniLM-L6-v2"
onnx_module.ONNXMiniLM_L6_V2.DOWNLOAD_PATH = workspace_cache

# Uses all-MiniLM-L6-v2 locally (free, zero quota)
_embed_fn = embedding_functions.DefaultEmbeddingFunction()

def get_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector using a local, open-source model.
    """
    # DefaultEmbeddingFunction expects a list and returns a list of lists
    return _embed_fn([text])[0]
