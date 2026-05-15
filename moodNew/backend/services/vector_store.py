import chromadb
from chromadb.config import Settings
from backend.services.embedder import Embedder

COLLECTION_NAME = "episodes_collection"
CHROMA_PATH = "./data/chromadb"


class VectorStore:
    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print(f"[VectorStore] Collection '{COLLECTION_NAME}' has {self.collection.count()} episodes")

    def is_empty(self) -> bool:
        return self.collection.count() == 0

    def add_episodes(self, episodes: list[dict]):
        """
        episodes: list of dicts with keys:
            id, semantic, show, season, episode, title, imdb_rating
        """
        ids = [ep["id"] for ep in episodes]
        documents = [ep["semantic"] for ep in episodes]
        metadatas = [
            {
                "show": ep["show"],
                "season": ep["season"],
                "episode": ep["episode"],
                "title": ep["title"],
                "imdb_rating": ep["imdb_rating"],
                "vibe": ep.get("vibe", ""),
                "mood_tags": ep.get("mood_tags", ""),
            }
            for ep in episodes
        ]
        embeddings = self.embedder.encode_batch(documents)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        print(f"[VectorStore] Added {len(ids)} episodes")

    def search(self, query: str, n_results: int = 5, disliked_ids: list[str] | None = None) -> tuple[
        list[dict], list[float]]:
        # 1. Кодируем запрос один раз
        query_vector = self.embedder.encode(query)
        disliked_set = set(disliked_ids or [])

        # 2. Используем уже готовый query_vector
        raw = self.collection.query(
            query_embeddings=[query_vector],
            n_results=n_results + len(disliked_set) + 5,
            include=["documents", "metadatas", "distances", "embeddings"],
        )

        candidates = []
        for i, doc_id in enumerate(raw["ids"][0]):
            if doc_id in disliked_set:
                continue
            meta = raw["metadatas"][0][i]
            candidates.append({
                "id": doc_id,
                "title": meta["title"],
                "show": meta["show"],
                "season": int(meta["season"]),
                "episode": int(meta["episode"]),
                "imdb_rating": float(meta.get("imdb_rating", 7.0)),
                "vibe": meta.get("vibe", ""),
                "mood_tags": meta.get("mood_tags", ""),
                "description": raw["documents"][0][i],
                "cosine_sim": 1 - raw["distances"][0][i],
                "embedding": raw["embeddings"][0][i],
            })

        # 3. Возвращаем И список, И вектор
        return candidates, query_vector


def _cosine(a: list[float], b: list[float]) -> float:
    import numpy as np
    a, b = np.array(a), np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0
