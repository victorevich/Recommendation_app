import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from backend.services.embedder import Embedder
from backend.services.vector_store import VectorStore


def parse_args():
    parser = argparse.ArgumentParser(description="Инициализация векторного хранилища MoodMatch")
    parser.add_argument("--csv", default="data/dataset-mood.csv", help="Путь к CSV-файлу с датасетом")
    parser.add_argument("--force", action="store_true", help="Пересоздать хранилище, если оно уже заполнено")
    return parser.parse_args()


def load_episodes(csv_path: str) -> list[dict]:
    print(f"[init_db] Читаем датасет: {csv_path}")
    df = pd.read_csv(csv_path)

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip('"')

    required = {"show", "season", "episode", "title", "imdb_rating", "semantic"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"В датасете отсутствуют колонки: {missing}")

    df = df.dropna(subset=["semantic"])

    episodes = []
    for _, row in df.iterrows():
        ep_id = (
            f"{row['show']}_{row['season']}_{row['episode']}"
            .replace(" ", "_")
            .replace('"', "")
        )
        episodes.append(
            {
                "id": ep_id,
                "semantic": row["semantic"],
                "show": row["show"],
                "season": int(row["season"]),
                "episode": int(row["episode"]),
                "title": row["title"],
                "imdb_rating": float(row["imdb_rating"]),
                "vibe": str(row.get("vibe", "") or ""),
                "mood_tags": str(row.get("mood_tags", "") or ""),
            }
        )

    print(f"[init_db] Загружено строк: {len(episodes)}")
    return episodes


def main():
    args = parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"[init_db] Файл не найден: {csv_path}")
        sys.exit(1)

    print("[init_db] Загружаем модель...")
    embedder = Embedder()
    store = VectorStore(embedder)

    if not store.is_empty():
        if args.force:
            print("[init_db] --force: удаляем старые данные...")
            store.client.delete_collection("episodes_collection")
            store.collection = store.client.get_or_create_collection(
                name="episodes_collection",
                metadata={"hnsw:space": "cosine"},
            )
        else:
            count = store.collection.count()
            print(f"[init_db] Хранилище уже содержит {count} эпизодов.")
            print("[init_db] Используйте --force для пересоздания.")
            sys.exit(0)

    episodes = load_episodes(str(csv_path))

    print("[init_db] Векторизация и запись в ChromaDB...")
    store.add_episodes(episodes)

    print(f"\n[init_db] ✓ Готово. В хранилище {store.collection.count()} эпизодов.")
    print("[init_db] Теперь запускайте сервер: uvicorn main:app --reload")


if __name__ == "__main__":
    main()