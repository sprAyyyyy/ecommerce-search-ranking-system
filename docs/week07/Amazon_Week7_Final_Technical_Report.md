# Amazon Search / Learning-to-Rank Project — Week 7 Final Report

## 1. Executive Summary

Week 7 focused on converting the previously developed retrieval and ranking experiments into a complete end-to-end search system.

The final system integrates:

- a 10,000-product Amazon catalog;
- SBERT query embeddings;
- FAISS dense candidate retrieval;
- Top-100 candidate generation;
- 29 ranking features covering lexical, semantic, multimodal, metadata, and interaction signals;
- the saved Week 5 LambdaMART model;
- a FastAPI search service;
- a Streamlit interactive demo;
- latency profiling, caching, validation, and deployment files.

The final Week 7 system satisfies the main roadmap requirement of **sub-200 ms retrieval + re-ranking latency**.

## 2. Final Architecture

User Query  
→ Streamlit Interface  
→ FastAPI `/search`  
→ SBERT Query Embedding  
→ FAISS Top-100 Retrieval  
→ 29 Runtime Ranking Features  
→ LambdaMART Re-ranking  
→ Top-K Ranked Products

See `week7_v4_architecture.png`.

## 3. V1 — Initial End-to-End Integration

The first integration successfully connected query embedding, FAISS retrieval, feature generation, and ranking. However, the initial implementation exposed two integration problems:

1. a Week 5 judged query-product table was initially treated as the retrieval catalog instead of the full Week 1 10K catalog;
2. the saved LambdaMART model required the exact Week 5 feature schema rather than a simplified temporary feature vector.

The corrected V1.1 pipeline therefore used:

- `cleaned_products_10k.parquet` as the full catalog;
- Week 4 SBERT embeddings aligned to that catalog;
- Week 4 CLIP image embeddings;
- the exact Week 5 runtime feature ordering;
- the saved Week 5 LambdaMART model.

All model/catalog/schema alignment checks passed.

## 4. Latency Optimization

The corrected V1.1 mean latency was approximately **212.86 ms**, slightly above the 200 ms roadmap target.

V1.3 optimized runtime without retraining or changing LambdaMART.

Optimizations included:

- loading only the CLIP text tower at query time;
- precomputing normalized catalog text and token sets;
- precomputing metadata arrays;
- vectorizing CLIP candidate similarity;
- caching SBERT query embeddings;
- caching CLIP query embeddings;
- reducing repeated pandas/string processing.

The resulting V1.3 performance was:

| Metric | Result |
|---|---:|
| Fresh-query mean | 83.94 ms |
| Fresh-query P95 | 99.91 ms |
| Cached-query mean | 28.84 ms |
| V1.1 → V1.3 latency reduction | 60.6% |

This moved the system comfortably below the 200 ms target.

## 5. V2 — FastAPI Service

The optimized pipeline was packaged as a FastAPI service.

Endpoints:

- `GET /`
- `GET /health`
- `POST /search`

A `/search` request accepts a natural-language query, `top_k`, and `candidate_k`, and returns ranked product results with ranking score, retrieval score, and latency breakdown.

Validated V2 API performance:

| Metric | Result |
|---|---:|
| Internal pipeline mean | 87.32 ms |
| API round-trip mean | 92.57 ms |
| API round-trip P95 | 119.59 ms |
| Mean latency target | PASS |

API validation also confirmed:

- 10K catalog loaded;
- FAISS contains 10K products;
- LambdaMART uses 29 features;
- `/health` returns HTTP 200;
- `/search` returns HTTP 200;
- invalid candidate counts return HTTP 422.

## 6. V3 — Streamlit Demo

A Streamlit interface was added on top of the production search pipeline.

The demo includes:

- natural-language query input;
- Top-K control;
- candidate-count control;
- product rank and title;
- brand and category;
- price, rating, and review count;
- image display when an image URL is available;
- LambdaMART ranking score;
- SBERT retrieval score;
- latency breakdown;
- explicit `<200 ms` performance status.

The demo supports both direct `SearchEngine` mode and API-backed mode.

## 7. V4 — Final Validation

Final validation status: **34/34 checks passed**.

Current V4 fresh-query recheck:

| Metric | Result |
|---|---:|
| Mean | 119.95 ms |
| Median | 116.83 ms |
| P95 | 149.07 ms |
| Maximum | 164.97 ms |
| Mean < 200 ms | PASS |

The system therefore remains functionally integrated after packaging and deployment-oriented refactoring.

## 8. Example Search Quality

Representative Top-3 results from the final pipeline:

- **best non drying lip stain**: Treat Black Cherry Lip &amp; Cheek Stain | Lipping Moisturizing Lip Tint, Long Lasting [All Day Formula] Glossy Liquid Lip Color Stain and Repair Balm [Non Smudge] with Keratin and Collagen - 15g - [Tango Red] | Lip Couture WATERPROOF Liquid Lipstick (poison apple)-Made in USA
- **came with no tanning mitt**: St Moriz Instant Self Tanning Mousse 2 x 200ml Dark With St Moriz Tanning Mitt | St. Moriz Advanced Pro Insta-Grad Tanning Mousse 200ml | Feel Glowing Self Tanning Mousse 6oz + Applicator Mitt
- **perfect scent for a romantic evening**: TEN By Intense for Men Male Pheromone Cologne 2 Oz | Bandit By Robert Piquet For Women. Shower Cream 8.5 Ounces | Fuck Me Perfume Eau de Parfum 2oz Sensual Fragrance Spray

These known-query smoke tests are intended as qualitative integration checks. Full ranking-quality claims remain tied to the offline judged-query evaluation from earlier weeks.

## 9. Engineering Deliverables

The final Week 7 package includes:

- modular `SearchEngine`;
- FastAPI application;
- Streamlit application;
- runtime artifacts;
- `requirements.txt`;
- Dockerfile;
- Docker Compose configuration;
- API tests;
- latency benchmarks;
- validation matrices;
- architecture diagram;
- latency-evolution visualization;
- final Week 7 report.

## 10. Key Result

Week 7 successfully transformed the earlier retrieval and Learning-to-Rank work into an operational end-to-end search application.

The strongest engineering result is the reduction of fresh-query latency from approximately **212.86 ms** to **83.94 ms**, a **60.6% reduction**, while retaining the full 10K catalog, Top-100 retrieval, multimodal feature generation, and the original saved LambdaMART ranker.

The FastAPI service also maintains a mean round-trip latency of approximately **92.57 ms**, comfortably within the Week 7 sub-200 ms objective.

## 11. Next Steps

The next development phase can focus on deployment and search-quality robustness rather than basic integration:

- larger or production-scale product catalog;
- persistent FAISS index loading;
- stronger image coverage;
- batch query processing;
- service-level observability;
- cache metrics and eviction policies;
- asynchronous request handling;
- model/version registry;
- online A/B testing;
- click and conversion feedback;
- retrieval and re-ranking monitoring.

Week 7 is complete from an end-to-end system integration perspective.
