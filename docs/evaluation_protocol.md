# Evaluation scopes and interpretation

The final report has multiple benchmarks and **they must not be combined into one model leaderboard**.

| Benchmark | Unit | Primary questions | Representative outputs |
|---|---|---|---|
| Fixed-candidate reranking | 200 queries | Is the given candidate set ordered correctly? | NDCG@10, MAP@10, MRR |
| Full-catalog retrieval | 200 queries | Are relevant candidates recovered from the catalog? | Recall@10, Recall@50, NDCG@10, MRR |
| Cold-start holdout | 45 queries | Does low-label adaptation work on held-out queries? | NDCG@10, NDCG@3, Recall@3, MRR |
| Serving | Prototype requests | Is the integrated path responsive? | Mean and P95 latency |

**Do not** compare the 0.9297 reranking NDCG to the 0.8066 full-catalog retrieval NDCG as if they came from the same task.

The fixed reranking set contains the judged relevant candidates, so Recall@10 can saturate and is not an informative primary measure of retrieval coverage. Report full-catalog recall separately.

Reranking gain relative to BM25:

```python
relative_gain = (0.9297 / 0.8032 - 1) * 100
# 15.75%
```

The report uses partially proxy-derived relevance judgments, so reported offline scores should not be presented as online production performance.
