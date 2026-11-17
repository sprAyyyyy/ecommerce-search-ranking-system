# Week 7 Deployment Architecture (report-based)

This document describes the implementation in the original **Week 7 Final Technical Report**, and not necessarily the current contents of `app/` until original source code has been staged.

## Data and inference flow

```text
User query
  -> Streamlit UI
  -> FastAPI POST /search
  -> SBERT query embedding
  -> FAISS Top-100 candidates (10,000-product catalog)
  -> exact 29-feature runtime schema
  -> saved Week 5 LambdaMART reranker
  -> top-k ranked products, scores and stage latencies
```

Runtime feature families combine lexical, semantic, multimodal, metadata and interaction signals. The Week 7 report describes three API endpoints: `GET /`, `GET /health` and `POST /search`.

### Example request from Week 7 report

```json
{"query":"best non drying lip stain","top_k":10,"candidate_k":100}
```

The reported response includes product IDs, titles, brand/category, image URLs when available, prices, ratings, review counts, LambdaMART scores, SBERT scores and stage latency.

## Separate latency measurements

| Benchmark | Mean latency | P95 |
|---|---:|---:|
| V1.1 integrated corrected pipeline | 212.86 ms | — |
| V1.3 optimized fresh-query pipeline | 83.94 ms | 99.91 ms |
| V2 API round-trip | 92.57 ms | 119.59 ms |
| V4 final packaged-system recheck | 119.95 ms | 149.07 ms |

These are different test executions. Do not present the optimized internal pipeline result as a guaranteed web API response time.

## How latency improved

The report describes loading only the CLIP text tower for query-time text encoding, precomputing normalized catalog text/tokens/lengths and metadata, vectorizing CLIP candidate similarities, caching query embeddings and reducing repeated pandas/string operations. It also documents **34/34** packaged-system checks passing during Week 7 V4.

## Import original source

See [Chinese source import guide](IMPORT_NEXT_STEPS_ZH.md). The original Week 7 ZIP also contains model weights and data artifacts; they should not be uploaded to the public repository without explicit permission. This note does not substitute for the real application source or installation instructions.
