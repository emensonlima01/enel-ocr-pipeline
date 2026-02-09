ARG PYTHON_VERSION=3.11.9
FROM python:${PYTHON_VERSION}-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        libopenblas0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY enel_ocr ./enel_ocr
COPY scripts ./scripts

EXPOSE 8000

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:8000 --workers ${WEB_CONCURRENCY:-$(nproc)} --threads ${WEB_THREADS:-1} --timeout 120 enel_ocr.api:app"]
