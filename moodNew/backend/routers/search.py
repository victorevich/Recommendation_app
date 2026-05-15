from fastapi import APIRouter, Request
from backend.models.schemas import SearchRequest, SearchResponse

router = APIRouter(prefix="/api", tags=["search"])


# backend/routers/search.py
categoryMap = {
  "love": "романтические отношения, первое свидание, поиск любви, химия между героями, влюбленность, бабочки в животе",
  "career": "карьерные амбиции, успех на работе, поиск призвания, офисные интриги, профессиональный рост, трудолюбие",
  "friends": "дружеская поддержка, верность, посиделки в баре с друзьями, общие секреты, взаимовыручка, крепкая дружба",
  "family": "семья, родители, дом, семейные праздники, поддержка родных, возвращение домой"
}


@router.post("/search", response_model=SearchResponse)
async def search(request: Request, body: SearchRequest):
    store = request.app.state.store
    ranker = request.app.state.ranker

    # 1. Определяем, по чему ищем
    search_query = body.query
    display_name = body.query  # то, что вернем для заголовка

    if body.category and body.category in categoryMap:
        search_query = categoryMap[body.category]
        display_name = body.category  # или просто оставить пустым, JS подменит

    # 2. Поиск
    candidates, query_vector = store.search(
        query=search_query,
        n_results=body.n_results,
        disliked_ids=body.disliked_ids,
    )

    # 3. Ранжирование
    ranked = ranker.rank(
        candidates,
        query_vec=query_vector,
        session_centroid=body.session_centroid,
        global_centroid=body.global_centroid,
    )

    top = ranked[:body.n_results]

    # 4. Проверка результата
    if not top or top[0]["score"] < 30:
        return SearchResponse(
            results=[],
            query=display_name,
            message="Не удалось найти подходящие серии."
        )

    for item in top:
        item.pop("embedding", None)
        item.pop("cosine_sim", None)

    # Возвращаем display_name вместо body.query
    return SearchResponse(results=top, query=display_name, message="")