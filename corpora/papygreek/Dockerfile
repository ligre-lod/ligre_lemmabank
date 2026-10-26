FROM python:3.12-slim

WORKDIR /app

COPY papygreek/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY papygreek/load_papygreek.py ./papygreek/load_papygreek.py

CMD ["python", "-m", "papygreek.load_papygreek"]
