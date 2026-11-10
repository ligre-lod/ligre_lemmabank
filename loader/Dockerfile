FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY load_lemmas.py lemma_corrections.py load_corpora.py ./loader/

CMD ["python", "loader/load_lemmas.py"]
