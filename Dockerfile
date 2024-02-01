# https://hub.docker.com/_/python
FROM python:3.10-slim-bookworm

ENV PYTHONUNBUFFERED True

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

EXPOSE 8000

CMD ["uvicorn", "battlechess.server.btchApi:app", "--host", "0.0.0.0", "--port", "8000"]
