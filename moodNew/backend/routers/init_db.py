from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from pydantic import BaseModel
import pandas as pd
import io

router = APIRouter(prefix="/api", tags=["admin"])


class InitResponse(BaseModel):
    loaded: int
    message: str


@router.post("/init-db", response_model=InitResponse)
async def init_db(request: Request, file: UploadFile = File(...)):
    store = request.app.state.store

    if not store.is_empty():
        raise HTTPException(
            status_code=409,
            detail="Collection already has data. Delete data/chromadb to reinitialize.",
        )

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))

    required = {"show", "season", "episode", "title", "imdb_rating", "semantic"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing columns: {missing}")

    df = df.dropna(subset=["semantic"])
    df["show"] = df["show"].str.strip('"')
    df["title"] = df["title"].str.strip('"')
    df["semantic"] = df["semantic"].str.strip('"')
    df["mood_tags"] = df.get("mood_tags", pd.Series([""] * len(df))).fillna("").str.strip('"')

    episodes = []
    for _, row in df.iterrows():
        ep_id = f"{row['show']}_{row['season']}_{row['episode']}".replace(" ", "_").replace('"', "")
        episodes.append(
            {
                "id": ep_id,
                "semantic": row["semantic"],
                "show": row["show"],
                "season": int(row["season"]),
                "episode": int(row["episode"]),
                "title": row["title"],
                "imdb_rating": float(row["imdb_rating"]),
                "mood_tags": row["mood_tags"],
            }
        )

    store.add_episodes(episodes)
    return InitResponse(loaded=len(episodes), message="Database initialized successfully")


@router.get("/db-status")
async def db_status(request: Request):
    store = request.app.state.store
    count = store.collection.count()
    return {"episodes_count": count, "is_empty": count == 0}
