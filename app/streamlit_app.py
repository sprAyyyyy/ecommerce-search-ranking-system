
import os
import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Amazon Search Ranking Demo",
    page_icon="🔎",
    layout="wide",
)

ROOT = Path(__file__).resolve().parent
API_URL = os.getenv("API_URL", "").strip().rstrip("/")


@st.cache_resource(show_spinner="Loading search models...")
def load_engine():
    from amazon_search_service.search_engine import SearchEngine
    return SearchEngine(
        artifact_dir=ROOT / "artifacts"
    )


def direct_search(query, top_k, candidate_k):
    engine = load_engine()
    return engine.search(
        query=query,
        top_k=top_k,
        candidate_k=candidate_k,
    )


def api_search(query, top_k, candidate_k):
    response = requests.post(
        f"{API_URL}/search",
        json={
            "query": query,
            "top_k": top_k,
            "candidate_k": candidate_k,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def do_search(query, top_k, candidate_k):
    if API_URL:
        return api_search(
            query,
            top_k,
            candidate_k
        )
    return direct_search(
        query,
        top_k,
        candidate_k
    )


def money(value):
    if value is None:
        return "N/A"
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "N/A"


def rating_text(value):
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.1f} / 5"
    except Exception:
        return "N/A"


st.title("Amazon Search Ranking Demo")
st.caption(
    "SBERT + FAISS Top-100 retrieval → "
    "29-feature LambdaMART re-ranking"
)

backend_name = (
    "FastAPI"
    if API_URL
    else "Direct SearchEngine"
)

with st.sidebar:
    st.header("Search settings")

    top_k = st.slider(
        "Results to return",
        min_value=3,
        max_value=20,
        value=10,
        step=1,
    )

    candidate_k = st.select_slider(
        "Retrieval candidates",
        options=[50, 75, 100, 150, 200],
        value=100,
    )

    st.divider()

    st.write("**Backend**")
    st.write(backend_name)

    st.write("**Catalog**")
    st.write("10,000 products")

    st.write("**Ranker**")
    st.write("LambdaMART — 29 features")

    st.write("**Week 7 target**")
    st.write("< 200 ms")

query = st.text_input(
    "Search products",
    value="best non drying lip stain",
    placeholder="Type a natural-language product query...",
)

search_clicked = st.button(
    "Search",
    type="primary",
    use_container_width=True,
)

if search_clicked:
    if not query.strip():
        st.warning("Please enter a search query.")
        st.stop()

    with st.spinner("Retrieving and re-ranking products..."):
        ui_start = time.perf_counter()

        try:
            payload = do_search(
                query.strip(),
                top_k,
                candidate_k,
            )
        except Exception as e:
            st.error(
                f"Search failed: {type(e).__name__}: {e}"
            )
            st.stop()

        ui_total_ms = (
            time.perf_counter() - ui_start
        ) * 1000

    latency = payload.get(
        "latency_ms",
        {}
    )

    total_ms = float(
        latency.get("total", ui_total_ms)
    )

    if total_ms < 200:
        latency_status = "PASS"
    else:
        latency_status = "ABOVE TARGET"

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Results",
        len(payload.get("results", []))
    )

    c2.metric(
        "Pipeline latency",
        f"{total_ms:.1f} ms"
    )

    c3.metric(
        "UI round trip",
        f"{ui_total_ms:.1f} ms"
    )

    c4.metric(
        "<200 ms target",
        latency_status
    )

    with st.expander(
        "Latency breakdown",
        expanded=False
    ):
        latency_rows = []

        for name in [
            "embedding",
            "retrieval",
            "features",
            "ranking",
            "total",
        ]:
            if name in latency:
                latency_rows.append({
                    "stage": name,
                    "latency_ms": round(
                        float(latency[name]),
                        3
                    )
                })

        if latency_rows:
            st.dataframe(
                pd.DataFrame(latency_rows),
                hide_index=True,
                use_container_width=True,
            )

    st.subheader(
        f"Ranked results for “{payload.get('query', query)}”"
    )

    results = payload.get(
        "results",
        []
    )

    if not results:
        st.info("No products returned.")
        st.stop()

    for item in results:
        rank = item.get("rank", "")
        title = item.get(
            "title",
            "Untitled product"
        )

        with st.container(border=True):
            image_col, text_col = st.columns(
                [1, 4]
            )

            image_url = item.get(
                "image_url"
            )

            with image_col:
                if image_url:
                    try:
                        st.image(
                            image_url,
                            use_container_width=True
                        )
                    except Exception:
                        st.write("No image")
                else:
                    st.write("No image")

            with text_col:
                st.markdown(
                    f"### #{rank} {title}"
                )

                brand = (
                    item.get("brand")
                    or "Unknown brand"
                )

                category = (
                    item.get("category")
                    or "Unknown category"
                )

                st.caption(
                    f"{brand} · {category}"
                )

                m1, m2, m3, m4 = st.columns(4)

                m1.metric(
                    "Price",
                    money(item.get("price"))
                )

                m2.metric(
                    "Rating",
                    rating_text(
                        item.get("average_rating")
                    )
                )

                reviews = item.get(
                    "review_count"
                )

                if reviews is None:
                    review_text = "N/A"
                else:
                    try:
                        review_text = f"{int(float(reviews)):,}"
                    except Exception:
                        review_text = "N/A"

                m3.metric(
                    "Reviews",
                    review_text
                )

                m4.metric(
                    "Rank score",
                    f"{float(item.get('ranking_score', 0)):.4f}"
                )

                st.caption(
                    "SBERT retrieval score: "
                    f"{float(item.get('retrieval_score', 0)):.4f}"
                )

    with st.expander(
        "Raw JSON-compatible result table",
        expanded=False
    ):
        st.dataframe(
            pd.DataFrame(results),
            hide_index=True,
            use_container_width=True,
        )

else:
    st.info(
        "Enter a natural-language query and click Search."
    )
