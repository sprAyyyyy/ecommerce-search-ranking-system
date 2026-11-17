# Reproducing the original 8-week experiments

This repository now includes **28 historical experiment notebooks** and the **Week 7 FastAPI/Streamlit source**. The files are authentic copies of the submitted source, with notebook outputs cleared. Reproducing the original reported performance requires original upstream ZIP artifacts and the corresponding Colab/model dependencies. The notebooks have not been executed as part of this publication preparation.

## Notebook navigation

Open `notebooks/week01` through `notebooks/week08` in ascending order. Each week has a short README and source notebook files. The original notebooks contain one-click Colab cells, but many rely on ZIP artifacts from preceding weeks. The complete raw archive is deliberately not published.

## Local API/demo reproduction

1. Keep your original `amazon internship.zip` locally; it is **not** part of this repository.
2. Run `python scripts/restore_local_runtime_artifacts.py --source "/path/to/amazon internship.zip"` from the repository root. This restores six required runtime files under ignored `app/artifacts/`.
3. Install `app/requirements.txt` in an isolated Python environment (the original package did not pin versions).
4. From `app/`, launch `python -m uvicorn amazon_search_service.main:app --host 127.0.0.1 --port 8000`.
5. Launch the frontend with `streamlit run streamlit_app.py` in `app/`, or set `API_URL=http://127.0.0.1:8000`.

The pipeline loads a 10K-product sample catalog, normalized SBERT embeddings, CLIP image embeddings, the saved LambdaMART model and its **29-feature runtime schema**. Downloading transformer model weights may require a network connection.

### API endpoints

- `GET /` — service metadata
- `GET /health` — loaded model/catalog health
- `POST /search` — query, `top_k`, `candidate_k` (must be >= `top_k`)

### Deployment caveat

No live hosting or independently reproduced latency is claimed here. The original Week 7 report measured 83.94 ms fresh-query mean in V1.3 optimization; separately, the packaged V4 recheck reported 119.95 ms mean. These are different runs.

## Security and publication

The public archive **excludes** product/review-level data, saved embeddings, trained model weights, PII-bearing manual-label examples and intermediary result ZIPs. It does include source code and published aggregate results. Before making your repository public, manually verify code ownership, permission to publish internship work, and upstream dataset licensing. Automatic scans cannot establish those rights.

The original datasets are described at https://nijianmo.github.io/amazon/.
