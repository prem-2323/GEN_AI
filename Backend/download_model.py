"""Pre-download and cache default embedding models (BAAI/bge-small-en-v1.5) for instant offline startup."""
import sys
import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"


def download_default_models() -> bool:
    model_name = "BAAI/bge-small-en-v1.5"
    print(f"[*] Verifying / caching default embedding model '{model_name}'...")
    try:
        from sentence_transformers import SentenceTransformer

        # Check if already present in local cache
        try:
            model = SentenceTransformer(model_name, local_files_only=True)
            print(f"  [OK] Model '{model_name}' is verified in local cache.")
        except Exception:
            print(f"  [*] Downloading '{model_name}' model weights from HuggingFace...")
            model = SentenceTransformer(model_name)
            print(f"  [OK] Model '{model_name}' downloaded and cached successfully.")

        get_dim = getattr(
            model,
            "get_embedding_dimension",
            getattr(model, "get_sentence_embedding_dimension", None),
        )
        dim = get_dim() if get_dim else 384
        print(f"  [OK] Embedding dimension: {dim}d ready.")
        return True
    except Exception as exc:
        print(f"  [ERROR] Failed to download embedding model '{model_name}': {exc}", file=sys.stderr)
        return False


if __name__ == "__main__":
    success = download_default_models()
    sys.exit(0 if success else 1)
