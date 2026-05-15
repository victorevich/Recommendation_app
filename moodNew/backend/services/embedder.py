from sentence_transformers import SentenceTransformer
import numpy as np


MODEL_NAME = "DeepPavlov/rubert-base-cased-sentence"


class Embedder:
    def __init__(self):
        print(f"[Embedder] Loading model: {MODEL_NAME}")
        self.model = SentenceTransformer(MODEL_NAME)
        print("[Embedder] Model ready")

    def encode(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=True)
        return vectors.tolist()
