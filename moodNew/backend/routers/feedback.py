import uuid
from fastapi import APIRouter, Request, Response
from backend.models.schemas import FeedbackRequest

router = APIRouter(prefix="/api", tags=["feedback"])

@router.post("/feedback")
async def feedback(request: Request, response: Response, body: FeedbackRequest):
    browser_id = request.cookies.get("session_id")
    if not browser_id:
        browser_id = str(uuid.uuid4())
        response.set_cookie("session_id", browser_id, httponly=True, max_age=60 * 60 * 24 * 30)

    store = request.app.state.pref_store
    liked = body.action == "like"

    if liked:
        store.update(browser_id, body.episode_embedding)
    global_vec = store.get_global_vector(browser_id)

    new_disliked = body.disliked_ids + ([] if liked else [body.episode_id])

    return {
        "global_vector": global_vec,
        "disliked_ids": new_disliked
    }