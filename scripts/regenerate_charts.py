"""Recreate three aggregate benchmark figures from the small results CSVs."""
from pathlib import Path
import csv
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]

def data(name):
    with (root/'results'/name).open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

def barh(names, values, title, xlabel, output, xlim=None):
    fig,ax=plt.subplots(figsize=(10,5.5))
    # Reorder to show highest value at the top.
    names=names[::-1];values=values[::-1]
    ax.barh(names,values)
    ax.set_xlabel(xlabel)
    ax.set_title(title,loc='left',fontweight='bold')
    if xlim: ax.set_xlim(*xlim)
    for i,v in enumerate(values):ax.text(v+max(values)*.008,i,f'{v:.4f}',va='center',fontsize=9)
    ax.spines[['top','right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(root/'assets'/output,dpi=160,bbox_inches='tight')
    plt.close(fig)

rank=data('reranking_benchmark.csv')
barh([x['model'] for x in rank],[float(x['ndcg_at_10']) for x in rank],
     'Ranking quality on fixed 200-query candidate set','NDCG@10','reranking_ndcg10.png',(0,1.04))
retr=data('full_catalog_retrieval_benchmark.csv')
barh([x['model'] for x in retr],[float(x['recall_at_50']) for x in retr],
     'Full-catalog retrieval coverage (separate scope)','Recall@50','retrieval_tradeoff.png',(0,.75))
ab=data('feature_ablation.csv')
barh([x['removed_feature_group'] for x in ab],[float(x['absolute_drop']) for x in ab],
     'Feature-group ablation from final reranker','Absolute drop in NDCG@10','feature_ablation.png',(0,.048))
print('Saved 3 charts in assets/.')
