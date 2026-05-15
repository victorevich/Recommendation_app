from pydantic import BaseModel, Field
from typing import List, Optional

class SearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    n_results: int = 5
    disliked_ids: List[str] = []
    session_centroid: Optional[List[float]] = None
    global_centroid: Optional[List[float]] = None

class SearchResponse(BaseModel):
    results: List[dict]
    query: str
    message: str


class EpisodeResult(BaseModel):
    id: str
    title: str
    show: str
    season: int
    episode: int
    imdb_rating: float
    vibe: str
    mood_tags: str
    description: str
    score: int


class FeedbackRequest(BaseModel):
    episode_id: str
    action: str  # "like" | "dislike"
    episode_embedding: list[float]
    browser_id: str
    session_centroid: list[float] | None = None
    disliked_ids: list[str] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    new_user_vector: list[float] | None
    query: str
    message: str
