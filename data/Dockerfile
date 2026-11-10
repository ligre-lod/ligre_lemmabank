FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY generate_lemma_data.py ./data/generate_lemma_data.py
COPY load_papygreek.py ./data/load_papygreek.py

CMD ["python", "data/generate_lemma_data.py"]
