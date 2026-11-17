# Week 7 FastAPI + Streamlit application source

Source imported from the original `amazon_week7_v4_final_package.zip` inside the supplied `amazon internship.zip`. The source files were preserved except the Dockerfile was corrected to copy the Streamlit entry point into the container.

**Not a hosted/live demo**: the trained LambdaMART model, product catalog, SBERT product embeddings, CLIP image embeddings and mapping are intentionally omitted from the GitHub archive. The service cannot start without them.

## Restore data and models on your own computer

From the repository root:

```bash
python scripts/restore_local_runtime_artifacts.py --source "/path/to/amazon internship.zip"
cd app
python -m pip install -r requirements.txt
python -m uvicorn amazon_search_service.main:app --host 127.0.0.1 --port 8000
```

UI in another terminal (from `app/`):

```bash
streamlit run streamlit_app.py
```

API-backed UI:

```bash
API_URL=http://127.0.0.1:8000 streamlit run streamlit_app.py
```

Windows PowerShell: `$env:API_URL="http://127.0.0.1:8000"` then `streamlit run streamlit_app.py`.

Once the local artifacts are restored, `docker compose up --build` can also build the source from within `app/`; this has not been executed here. The Hugging Face SBERT and CLIP text models may need to download on first run.

API example:

```json
{ "query": "best non drying lip stain", "top_k": 10, "candidate_k": 100 }
```

See `docs/week07/` for technical validation from the source package. Reported latency was measured in the original experiment environment, not from this GitHub packaging exercise.
