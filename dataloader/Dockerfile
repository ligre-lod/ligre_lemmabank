FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY generate_lemma_data.py ./dataloader/generate_lemma_data.py
COPY export_ttl.py ./dataloader/export_ttl.py

CMD ["python", "dataloader/generate_lemma_data.py"]
