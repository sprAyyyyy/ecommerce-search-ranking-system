
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from .search_engine import SearchEngine


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=500
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50
    )
    candidate_k: int = Field(
        default=100,
        ge=1,
        le=500
    )


class ProductResult(BaseModel):
    rank: int
    product_id: str
    title: str
    category: str
    brand: str
    image_url: Optional[str] = None
    price: Optional[float] = None
    average_rating: Optional[float] = None
    review_count: Optional[float] = None
    ranking_score: float
    retrieval_score: float


class LatencyBreakdown(BaseModel):
    embedding: float
    retrieval: float
    features: float
    ranking: float
    total: float


class SearchResponse(BaseModel):
    query: str
    top_k: int
    candidate_k: int
    results: List[ProductResult]
    latency_ms: LatencyBreakdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = SearchEngine()
    yield


app = FastAPI(
    title="Amazon Search Ranking API",
    version="7.2",
    description=(
        "Week 7 V2: SBERT + FAISS Top-100 retrieval "
        "+ 29-feature LambdaMART re-ranking."
    ),
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "service": "Amazon Search Ranking API",
        "version": "7.2",
        "docs": "/docs",
        "health": "/health",
        "search": "/search",
    }


@app.get("/health")
def health(request: Request):
    return request.app.state.engine.health()


@app.post(
    "/search",
    response_model=SearchResponse
)
def search(
    payload: SearchRequest,
    request: Request
):
    try:
        if payload.candidate_k < payload.top_k:
            raise ValueError(
                "candidate_k must be >= top_k"
            )

        return request.app.state.engine.search(
            query=payload.query,
            top_k=payload.top_k,
            candidate_k=payload.candidate_k,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {type(e).__name__}: {e}"
        )
