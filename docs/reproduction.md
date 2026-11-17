# Reproduction and source import guide

## Source selection

The source project contained multiple versioned Colab notebooks. Prefer these representative **original file names**, where available:

- Week 1: `Amazon_2018_Week1_Preprocessing_V4.ipynb`, `Amazon_2018_Week1_V4_EDA_Visual.ipynb`
- Week 2: `Amazon_Week2_Baseline_Ranking_OneClick_Colab.ipynb`
- Week 3: `Amazon_Week3_Full_Week_OneClick_v2_ColabFix.ipynb`
- Week 4: `Amazon_Week4_V1_OneClick_SBERT_FAISS.ipynb`, `Amazon_Week4_V2_OneClick_CLIP_Multimodal_FIXED.ipynb`, `Amazon_Week4_V3_OneClick_CoverageAware_Hybrid_FIXED.ipynb`, `Amazon_Week4_V4_FinalValidation_OneClick.ipynb`
- Week 5: `Amazon_Week5_V2_LambdaMART_OneClick.ipynb`, `Amazon_Week5_V3_Model_Comparison_Ablation_OneClick.ipynb`, `Amazon_Week5_V4_ListNet_OneClick_FIXED.ipynb`
- Week 6: `Amazon_Week6_V1_ColdStart_Benchmark_OneClick.ipynb`, `Amazon_Week6_V2_FIXED_ZeroShot_Ranking_Adapter_OneClick.ipynb`, `Amazon_Week6_V3_FAST_QueryBatch_LLM_Relevance_OneClick.ipynb`, `Amazon_Week6_V4_Final_Evaluation_Ablation_OneClick.ipynb`
- Week 7: `Amazon_Week7_V1_3_Latency_Optimized.ipynb`, `Amazon_Week7_V2_FastAPI_Service_OneClick.ipynb`, `Amazon_Week7_V3_Streamlit_Demo_OneClick.ipynb`, `Amazon_Week7_V4_Final_Evaluation_OneClick.ipynb`
- Week 8: `Amazon_Week8_V1_Final_Benchmark_OneClick.ipynb`, `Amazon_Week8_V2_Ablation_Progression_OneClick.ipynb`, `Amazon_Week8_V3_Error_Analysis_OneClick.ipynb`, `Amazon_Week8_V4_Final_Package_OneClick.ipynb`

## Import notebooks

Put downloaded `.ipynb` files in one folder (subfolders are fine), then from this repository root:

```bash
python scripts/import_notebooks.py --source "/path/to/original/amazon-project"
python scripts/import_notebooks.py --source "/path/to/original/amazon-project" --apply
python scripts/preflight_repo.py
```

The import script uses a **conservative allowlist** of known notebook filenames and strips saved cell outputs, preventing accidental upload of extensive outputs or embedded private data. It does not import ZIPs, model checkpoints, raw product metadata or any PDF. Inspect notebooks for credentials, external paths, sensitive data, and redistribution permissions before committing.

## Data and dependent artifacts

Read the notebook's top markdown cell for its required upstream ZIP names. For example, the Week 8 V4 packaging notebook requires three separate Week 8 result archives. **Uploading only the final Week 8 ZIP is not sufficient to reproduce all earlier experiments.** Run upstream notebooks in order, or provide the required intermediates locally. Do not store large or restricted source files in GitHub.

## Runtime

- Python 3 notebooks built around Google Colab and user-uploaded artifacts.
- Retrieval stack: pandas, scikit-learn, BM25, sentence-transformers, FAISS, CLIP.
- Ranking stack: XGBoost, LambdaMART and ListNet.
- Serving prototype: FastAPI and Streamlit.
- Week 3 query understanding: local Llama 3 via Ollama.

Exact package versions, model artifacts, API start commands, and downloadable public data links **must be extracted and validated against the original source notebooks** before a one-command end-to-end reproduction claim can be made. Do not blindly install all optional stacks into the same environment.

## Adding the original report

Place your reviewed `Amazon_Week8_Final_Technical_Report_Revised.pdf` at `docs/final_technical_report.pdf` after confirming it contains nothing restricted or proprietary. GitHub will render PDFs in the repository browser.
