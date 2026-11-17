"""Import allowed original Week 1-8 Colab notebooks, removing saved outputs.

Safe default is dry run.  Does NOT run notebooks or process ZIP archives.
"""
import argparse, json, re
from pathlib import Path

ALLOWED = {
 'Amazon_2018_Week1_Preprocessing_V4.ipynb',
 'Amazon_2018_Week1_V4_EDA_Visual.ipynb',
 'Amazon_Week2_Baseline_Ranking_OneClick_Colab.ipynb',
 'Amazon_Week3_Full_Week_OneClick_v2_ColabFix.ipynb',
 'Amazon_Week4_V1_OneClick_SBERT_FAISS.ipynb',
 'Amazon_Week4_V2_OneClick_CLIP_Multimodal_FIXED.ipynb',
 'Amazon_Week4_V3_OneClick_CoverageAware_Hybrid_FIXED.ipynb',
 'Amazon_Week4_V4_FinalValidation_OneClick.ipynb',
 'Amazon_Week5_V2_LambdaMART_OneClick.ipynb',
 'Amazon_Week5_V3_Model_Comparison_Ablation_OneClick.ipynb',
 'Amazon_Week5_V4_ListNet_OneClick_FIXED.ipynb',
 'Amazon_Week6_V1_ColdStart_Benchmark_OneClick.ipynb',
 'Amazon_Week6_V2_FIXED_ZeroShot_Ranking_Adapter_OneClick.ipynb',
 'Amazon_Week6_V3_FAST_QueryBatch_LLM_Relevance_OneClick.ipynb',
 'Amazon_Week6_V4_Final_Evaluation_Ablation_OneClick.ipynb',
 'Amazon_Week7_V1_3_Latency_Optimized.ipynb',
 'Amazon_Week7_V2_FastAPI_Service_OneClick.ipynb',
 'Amazon_Week7_V3_Streamlit_Demo_OneClick.ipynb',
 'Amazon_Week7_V4_Final_Evaluation_OneClick.ipynb',
 'Amazon_Week8_V1_Final_Benchmark_OneClick.ipynb',
 'Amazon_Week8_V2_Ablation_Progression_OneClick.ipynb',
 'Amazon_Week8_V3_Error_Analysis_OneClick.ipynb',
 'Amazon_Week8_V4_Final_Package_OneClick.ipynb',
}

def clean_notebook(path):
    nb=json.loads(path.read_text(encoding='utf-8'))
    if nb.get('nbformat')!=4 or not isinstance(nb.get('cells'),list):
        raise ValueError(f'Unsupported notebook format: {path}')
    for cell in nb['cells']:
        if cell.get('cell_type')=='code':
            cell['outputs']=[]
            cell['execution_count']=None
        metadata=cell.get('metadata',{})
        if isinstance(metadata,dict):
            metadata.pop('execution',None)
            metadata.pop('collapsed',None)
    return json.dumps(nb,ensure_ascii=False,indent=1)+'\n'

parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,required=True,help='Your folder of downloaded original .ipynb files')
parser.add_argument('--apply',action='store_true',help='Actually copy cleaned notebooks; omitted by default')
args=parser.parse_args()
source=args.source.expanduser().resolve()
root=Path(__file__).resolve().parents[1]
if not source.is_dir(): parser.error(f'Source folder does not exist: {source}')
files=[p for p in source.rglob('*.ipynb') if p.name in ALLOWED]
by_name={}
for file in files:
    # Prefer the larger/most complete copy if files were downloaded more than once.
    previous=by_name.get(file.name)
    if previous is None or file.stat().st_size>previous.stat().st_size:
        by_name[file.name]=file
print(f'Matched {len(by_name)} of {len(ALLOWED)} approved original notebooks.')
for name,path in sorted(by_name.items()):
    match=re.search(r'Week([1-8])',name,re.I)
    week='week'+match.group(1) if match else 'week1'
    dest=root/'notebooks'/week/name
    print(('COPY ' if args.apply else 'PLAN ')+f'{path} -> {dest}')
    if args.apply:
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(clean_notebook(path),encoding='utf-8')
if not args.apply: print('Dry run complete. Add --apply to copy cleaned notebooks.')
print('Review code cells and metadata before publishing; output stripping is not a secret scan.')
