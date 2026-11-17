
from pathlib import Path
from functools import lru_cache
import json
import re
import time

import faiss
import lightgbm as lgb
import numpy as np
import pandas as pd
import torch

from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, CLIPTextModelWithProjection


class SearchEngine:
    def __init__(self, artifact_dir=None):
        self.artifact_dir = Path(
            artifact_dir or (
                Path(__file__).resolve().parent.parent / "artifacts"
            )
        )

        with open(self.artifact_dir / "runtime_config.json", "r") as f:
            cfg = json.load(f)

        self.feature_cols = cfg["feature_cols"]
        self.train_medians = cfg["train_medians"]
        self.sbert_model_name = cfg["sbert_model_name"]
        self.clip_model_name = cfg["clip_model_name"]

        self.catalog = pd.read_parquet(
            self.artifact_dir / "catalog.parquet"
        ).reset_index(drop=True)

        for c in ["product_id", "title", "description", "category", "brand"]:
            if c not in self.catalog.columns:
                self.catalog[c] = ""
            self.catalog[c] = self.catalog[c].fillna("").astype(str)

        for c in ["price", "average_rating", "review_count"]:
            if c not in self.catalog.columns:
                self.catalog[c] = np.nan
            self.catalog[c] = pd.to_numeric(
                self.catalog[c], errors="coerce"
            )

        self.sbert_product_emb = np.load(
            self.artifact_dir / "sbert_product_embeddings.npy"
        ).astype(np.float32)

        self.sbert_product_emb /= np.clip(
            np.linalg.norm(
                self.sbert_product_emb,
                axis=1,
                keepdims=True
            ),
            1e-12,
            None
        )

        self.clip_img_emb = np.load(
            self.artifact_dir / "clip_image_embeddings.npy"
        ).astype(np.float32)

        self.clip_img_emb /= np.clip(
            np.linalg.norm(
                self.clip_img_emb,
                axis=1,
                keepdims=True
            ),
            1e-12,
            None
        )

        self.clip_map = pd.read_csv(
            self.artifact_dir / "clip_embedding_map.csv"
        )
        self.clip_map["product_id"] = (
            self.clip_map["product_id"].astype(str)
        )
        if "clip_row" not in self.clip_map.columns:
            self.clip_map["clip_row"] = np.arange(len(self.clip_map))

        if len(self.catalog) != len(self.sbert_product_emb):
            raise ValueError(
                "Catalog/SBERT embedding alignment mismatch"
            )

        if len(self.clip_map) != len(self.clip_img_emb):
            raise ValueError(
                "CLIP embedding/map alignment mismatch"
            )

        self.N = len(self.catalog)

        self.sbert_model = SentenceTransformer(
            self.sbert_model_name
        )

        self.faiss_index = faiss.IndexFlatIP(
            self.sbert_product_emb.shape[1]
        )
        self.faiss_index.add(
            self.sbert_product_emb.astype(np.float32)
        )

        self.ranker = lgb.Booster(
            model_file=str(
                self.artifact_dir / "lambdamart_model.txt"
            )
        )

        if self.ranker.num_feature() != len(self.feature_cols):
            raise ValueError(
                "LambdaMART feature schema mismatch: "
                f"{self.ranker.num_feature()} vs "
                f"{len(self.feature_cols)}"
            )

        self.clip_device = (
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.clip_tokenizer = AutoTokenizer.from_pretrained(
            self.clip_model_name
        )
        self.clip_text_model = (
            CLIPTextModelWithProjection
            .from_pretrained(self.clip_model_name)
            .to(self.clip_device)
        )
        self.clip_text_model.eval()

        self._precompute_catalog_arrays()

    def _precompute_catalog_arrays(self):
        self.token_re = re.compile(r"[a-z0-9]+")

        self.PID = self.catalog["product_id"].astype(str).to_numpy()
        self.TITLE = self.catalog["title"].astype(str).to_numpy()
        self.DESC = self.catalog["description"].astype(str).to_numpy()
        self.CATEGORY = self.catalog["category"].astype(str).to_numpy()
        self.BRAND = self.catalog["brand"].astype(str).to_numpy()

        self.DOCUMENT = np.char.add(
            np.char.add(self.TITLE.astype(str), " "),
            self.DESC.astype(str)
        )

        self.RAW_PRICE = pd.to_numeric(
            self.catalog["price"], errors="coerce"
        ).to_numpy(dtype=np.float32)

        self.RAW_RATING = pd.to_numeric(
            self.catalog["average_rating"], errors="coerce"
        ).to_numpy(dtype=np.float32)

        self.RAW_REVIEWS = pd.to_numeric(
            self.catalog["review_count"], errors="coerce"
        ).to_numpy(dtype=np.float32)

        self.TITLE_NORM = np.array(
            [self._norm_text(x) for x in self.TITLE],
            dtype=object
        )
        self.BRAND_NORM = np.array(
            [self._norm_text(x) for x in self.BRAND],
            dtype=object
        )

        self.TITLE_TOKENS = [
            self._tokenize(x) for x in self.TITLE
        ]
        self.DESC_TOKENS = [
            self._tokenize(x) for x in self.DESC
        ]
        self.DOC_TOKENS = [
            self._tokenize(x) for x in self.DOCUMENT
        ]

        self.TITLE_TOKEN_SETS = [
            set(x) for x in self.TITLE_TOKENS
        ]
        self.DESC_TOKEN_SETS = [
            set(x) for x in self.DESC_TOKENS
        ]
        self.CATEGORY_TOKEN_SETS = [
            set(self._tokenize(x)) for x in self.CATEGORY
        ]

        self.TITLE_LEN = np.array(
            [len(x) for x in self.TITLE_TOKENS],
            dtype=np.float32
        )
        self.DESC_LEN = np.array(
            [len(x) for x in self.DESC_TOKENS],
            dtype=np.float32
        )

        pid_to_catalog = {
            pid: i for i, pid in enumerate(self.PID)
        }

        self.clip_row_by_catalog = np.full(
            self.N, -1, dtype=np.int32
        )

        for pid, row in zip(
            self.clip_map["product_id"].astype(str),
            self.clip_map["clip_row"].astype(int)
        ):
            i = pid_to_catalog.get(pid)
            if i is not None:
                self.clip_row_by_catalog[i] = int(row)

        self.image_col = None
        for c in [
            "image_url", "image", "large_image",
            "main_image", "imageURLHigh", "imageURL"
        ]:
            if c in self.catalog.columns:
                self.image_col = c
                break

        if self.image_col is not None:
            self.IMAGE = (
                self.catalog[self.image_col]
                .fillna("")
                .astype(str)
                .to_numpy()
            )
        else:
            self.IMAGE = np.array(
                [""] * self.N,
                dtype=object
            )

    def _tokenize(self, text):
        return self.token_re.findall(str(text).lower())

    @staticmethod
    def _norm_text(x):
        x = "" if pd.isna(x) else str(x).lower()
        x = re.sub(r"[^a-z0-9\s]+", " ", x)
        return re.sub(r"\s+", " ", x).strip()

    @staticmethod
    def _minmax(x):
        x = np.asarray(x, dtype=np.float32)
        if len(x) == 0:
            return x

        lo = float(np.nanmin(x))
        hi = float(np.nanmax(x))

        if (
            not np.isfinite(lo)
            or not np.isfinite(hi)
            or hi <= lo
        ):
            return np.zeros(
                len(x),
                dtype=np.float32
            )

        return (
            (x - lo) / (hi - lo)
        ).astype(np.float32)

    @lru_cache(maxsize=512)
    def _sbert_query(self, query):
        return self.sbert_model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype(np.float32)[0]

    @lru_cache(maxsize=512)
    def _clip_query(self, query):
        batch = self.clip_tokenizer(
            [query],
            padding=True,
            truncation=True,
            max_length=77,
            return_tensors="pt"
        ).to(self.clip_device)

        with torch.inference_mode():
            out = self.clip_text_model(**batch)
            feat = out.text_embeds
            feat = feat / feat.norm(
                p=2,
                dim=-1,
                keepdim=True
            ).clamp_min(1e-12)

        return (
            feat.detach()
            .cpu()
            .numpy()
            .astype(np.float32)[0]
        )

    def clear_caches(self):
        self._sbert_query.cache_clear()
        self._clip_query.cache_clear()

    def _build_features(
        self,
        query,
        candidate_idx,
        sbert_scores
    ):
        idx = np.asarray(
            candidate_idx,
            dtype=np.int64
        )
        n = len(idx)

        q_tokens = self._tokenize(query)
        q_set = set(q_tokens)
        q_norm = self._norm_text(query)

        docs = [
            self.DOCUMENT[i]
            for i in idx
        ]

        tokenized_docs = [
            self.DOC_TOKENS[i]
            for i in idx
        ]

        bm25 = BM25Okapi(tokenized_docs)
        bm25_score = np.asarray(
            bm25.get_scores(q_tokens),
            dtype=np.float32
        )

        tfidf = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            min_df=1
        )
        Xtf = tfidf.fit_transform(
            [query] + docs
        )

        tfidf_similarity = cosine_similarity(
            Xtf[0:1],
            Xtf[1:]
        ).ravel().astype(np.float32)

        raw_price = self.RAW_PRICE[idx]
        raw_rating = self.RAW_RATING[idx]
        raw_reviews = self.RAW_REVIEWS[idx]

        price_missing = np.isnan(
            raw_price
        ).astype(np.float32)

        rating_missing = np.isnan(
            raw_rating
        ).astype(np.float32)

        price = np.where(
            np.isnan(raw_price),
            self.train_medians["price"],
            raw_price
        ).astype(np.float32)

        rating = np.where(
            np.isnan(raw_rating),
            self.train_medians["average_rating"],
            raw_rating
        ).astype(np.float32)

        reviews = np.where(
            np.isnan(raw_reviews),
            self.train_medians["review_count"],
            raw_reviews
        ).astype(np.float32)
        reviews = np.clip(
            reviews,
            0,
            None
        )

        query_len = np.full(
            n,
            len(q_tokens),
            dtype=np.float32
        )

        title_len = self.TITLE_LEN[idx]
        description_len = self.DESC_LEN[idx]

        if q_set:
            denom = float(len(q_set))

            query_title_overlap = np.array(
                [
                    len(q_set & self.TITLE_TOKEN_SETS[i])
                    / denom
                    for i in idx
                ],
                dtype=np.float32
            )

            query_description_overlap = np.array(
                [
                    len(q_set & self.DESC_TOKEN_SETS[i])
                    / denom
                    for i in idx
                ],
                dtype=np.float32
            )

            query_title_token_coverage = (
                query_title_overlap.copy()
            )

            category_token_match = np.array(
                [
                    len(q_set & self.CATEGORY_TOKEN_SETS[i])
                    / denom
                    for i in idx
                ],
                dtype=np.float32
            )
        else:
            query_title_overlap = np.zeros(
                n, dtype=np.float32
            )
            query_description_overlap = np.zeros(
                n, dtype=np.float32
            )
            query_title_token_coverage = np.zeros(
                n, dtype=np.float32
            )
            category_token_match = np.zeros(
                n, dtype=np.float32
            )

        sbert_similarity = np.asarray(
            sbert_scores,
            dtype=np.float32
        )
        sbert_available = np.ones(
            n,
            dtype=np.float32
        )

        q_clip = self._clip_query(query)

        rows = self.clip_row_by_catalog[idx]
        valid_clip = rows >= 0

        clip_similarity = np.zeros(
            n,
            dtype=np.float32
        )

        clip_available = valid_clip.astype(
            np.float32
        )

        if valid_clip.any():
            clip_similarity[valid_clip] = (
                self.clip_img_emb[
                    rows[valid_clip]
                ] @ q_clip
            ).astype(np.float32)

        selected_title_norm = self.TITLE_NORM[idx]
        selected_brand_norm = self.BRAND_NORM[idx]

        exact_title_match = np.fromiter(
            (
                float(t == q_norm)
                for t in selected_title_norm
            ),
            dtype=np.float32,
            count=n
        )

        query_in_title = np.fromiter(
            (
                float(
                    bool(q_norm)
                    and q_norm in t
                )
                for t in selected_title_norm
            ),
            dtype=np.float32,
            count=n
        )

        brand_in_query = np.fromiter(
            (
                float(
                    bool(b)
                    and b in q_norm
                )
                for b in selected_brand_norm
            ),
            dtype=np.float32,
            count=n
        )

        log_review_count = np.log1p(
            reviews
        ).astype(np.float32)

        log_price = np.log1p(
            np.clip(
                price,
                0,
                None
            )
        ).astype(np.float32)

        data = {
            "bm25_score": bm25_score,
            "tfidf_similarity": tfidf_similarity,
            "price": price,
            "average_rating": rating,
            "review_count": reviews,
            "log_review_count": log_review_count,
            "price_missing": price_missing,
            "query_len": query_len,
            "title_len": title_len,
            "description_len": description_len,
            "query_title_overlap": query_title_overlap,
            "query_description_overlap": query_description_overlap,
            "sbert_similarity": sbert_similarity,
            "clip_similarity": clip_similarity,
            "sbert_available": sbert_available,
            "clip_available": clip_available,
            "log_price": log_price,
            "log_review_count_w5": log_review_count,
            "rating_missing_w5": rating_missing,
            "price_missing_w5": price_missing,
            "exact_title_match": exact_title_match,
            "query_in_title": query_in_title,
            "query_title_token_coverage":
                query_title_token_coverage,
            "brand_in_query": brand_in_query,
            "category_token_match": category_token_match,
            "bm25_score_qnorm":
                self._minmax(bm25_score),
            "tfidf_similarity_qnorm":
                self._minmax(tfidf_similarity),
            "sbert_similarity_qnorm":
                self._minmax(sbert_similarity),
            "clip_similarity_qnorm":
                self._minmax(clip_similarity),
        }

        X = pd.DataFrame(data)

        missing = [
            c for c in self.feature_cols
            if c not in X.columns
        ]

        if missing:
            raise ValueError(
                "Runtime features missing: "
                + ", ".join(missing)
            )

        X = X[
            self.feature_cols
        ].astype(np.float32)

        return (
            X.replace(
                [np.inf, -np.inf],
                0
            )
            .fillna(0)
        )

    def search(
        self,
        query,
        top_k=10,
        candidate_k=100
    ):
        query = str(query).strip()

        if not query:
            raise ValueError(
                "query must not be empty"
            )

        top_k = int(top_k)
        candidate_k = int(candidate_k)

        if top_k < 1 or top_k > 50:
            raise ValueError(
                "top_k must be between 1 and 50"
            )

        if candidate_k < top_k:
            raise ValueError(
                "candidate_k must be >= top_k"
            )

        candidate_k = min(
            candidate_k,
            500,
            self.N
        )

        t_total = time.perf_counter()

        t0 = time.perf_counter()
        q_emb = self._sbert_query(query)
        embedding_ms = (
            time.perf_counter() - t0
        ) * 1000

        t0 = time.perf_counter()
        scores, indices = self.faiss_index.search(
            q_emb.reshape(1, -1),
            candidate_k
        )
        candidate_idx = indices[0]
        sbert_scores = scores[0]
        retrieval_ms = (
            time.perf_counter() - t0
        ) * 1000

        t0 = time.perf_counter()
        X = self._build_features(
            query,
            candidate_idx,
            sbert_scores
        )
        features_ms = (
            time.perf_counter() - t0
        ) * 1000

        t0 = time.perf_counter()
        ranking_scores = np.asarray(
            self.ranker.predict(X),
            dtype=np.float32
        )
        ranking_ms = (
            time.perf_counter() - t0
        ) * 1000

        order = np.argsort(
            -ranking_scores
        )[:top_k]

        top_idx = candidate_idx[order]

        results = []

        for rank_no, (
            catalog_idx,
            candidate_pos
        ) in enumerate(
            zip(top_idx, order),
            start=1
        ):
            price = self.RAW_PRICE[catalog_idx]
            rating = self.RAW_RATING[catalog_idx]
            review_count = self.RAW_REVIEWS[catalog_idx]

            results.append({
                "rank": rank_no,
                "product_id": str(
                    self.PID[catalog_idx]
                ),
                "title": str(
                    self.TITLE[catalog_idx]
                ),
                "category": str(
                    self.CATEGORY[catalog_idx]
                ),
                "brand": str(
                    self.BRAND[catalog_idx]
                ),
                "image_url": (
                    str(self.IMAGE[catalog_idx])
                    if self.IMAGE[catalog_idx]
                    else None
                ),
                "price": (
                    None
                    if np.isnan(price)
                    else float(price)
                ),
                "average_rating": (
                    None
                    if np.isnan(rating)
                    else float(rating)
                ),
                "review_count": (
                    None
                    if np.isnan(review_count)
                    else float(review_count)
                ),
                "ranking_score": float(
                    ranking_scores[candidate_pos]
                ),
                "retrieval_score": float(
                    sbert_scores[candidate_pos]
                ),
            })

        total_ms = (
            time.perf_counter() - t_total
        ) * 1000

        return {
            "query": query,
            "top_k": top_k,
            "candidate_k": candidate_k,
            "results": results,
            "latency_ms": {
                "embedding": embedding_ms,
                "retrieval": retrieval_ms,
                "features": features_ms,
                "ranking": ranking_ms,
                "total": total_ms,
            }
        }

    def health(self):
        return {
            "status": "ok",
            "catalog_products": int(self.N),
            "faiss_products": int(
                self.faiss_index.ntotal
            ),
            "ranker_features": int(
                self.ranker.num_feature()
            ),
            "device": self.clip_device,
        }
