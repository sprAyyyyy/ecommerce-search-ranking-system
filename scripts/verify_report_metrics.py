"""Verify README's key results against report-transcribed CSV summaries."""
from pathlib import Path
import csv, math
ROOT=Path(__file__).resolve().parents[1]

def read(name):
    with (ROOT/'results'/name).open(newline='',encoding='utf-8') as fh:
        return list(csv.DictReader(fh))

def pick(rows, model, key):
    return float(next(row[key] for row in rows if row['model']==model))

def near(actual, expected, tolerance=0.0001):
    if not math.isclose(actual,expected,rel_tol=0,abs_tol=tolerance):
        raise AssertionError(f'Expected {expected}, observed {actual}')

rank=read('reranking_benchmark.csv')
cold=read('coldstart_benchmark.csv')
retr=read('full_catalog_retrieval_benchmark.csv')
latency=read('serving_latency.csv')
near(pick(rank,'LambdaMART','ndcg_at_10'),0.9297)
near(pick(rank,'BM25','ndcg_at_10'),0.8032)
gain=(pick(rank,'LambdaMART','ndcg_at_10')/pick(rank,'BM25','ndcg_at_10')-1)*100
near(gain,15.75,0.01)
near(pick(cold,'ZeroShot+LLM','ndcg_at_10'),0.8990)
near(pick(retr,'BM25','recall_at_50'),0.6442)
near(float(next(x['latency_ms'] for x in latency if x['metric']=='V1.3 fresh mean latency')),83.94)
print('PASS: Aggregate snapshot is internally consistent.')
print(f'Reranking LambdaMART vs BM25 relative NDCG@10 improvement: {gain:.2f}%')
print('NOTE: This verifies transcribed aggregates; it does not rerun model training.')
