import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from backend.services.vector_store import VectorStore
from backend.services.embedder import Embedder
from backend.services.ranker import Ranker
from backend.routers import search, feedback, init_db
from backend.services.preference_store import PreferenceStore

@asynccontextmanager
async def lifespan(app: FastAPI):
    embedder = Embedder()
    store = VectorStore(embedder)
    ranker = Ranker()
    pref_store = PreferenceStore()
    app.state.store = store
    app.state.ranker = ranker
    app.state.pref_store = pref_store
    yield


app = FastAPI(title="MoodMatch API", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")
app.state.templates = templates

app.include_router(search.router)
app.include_router(feedback.router)
app.include_router(init_db.router)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")
