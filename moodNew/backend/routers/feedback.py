from fastapi import APIRouter, Request
from backend.models.schemas import FeedbackRequest

router = APIRouter(prefix="/api", tags=["feedback"])

@router.post("/feedback")
async def feedback(request: Request, body: FeedbackRequest):
    store = request.app.state.pref_store
    liked = body.action == "like"

    if liked:
        store.update(body.browser_id, body.episode_embedding)

    global_vec = store.get_global_vector(body.browser_id)

    new_disliked = body.disliked_ids + ([] if liked else [body.episode_id])

    return {
        "global_vector": global_vec,
        "disliked_ids": new_disliked
    }