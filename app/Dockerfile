FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY amazon_search_service ./amazon_search_service
COPY streamlit_app.py run_demo.py ./
COPY artifacts ./artifacts

EXPOSE 8000

CMD ["uvicorn", "amazon_search_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
