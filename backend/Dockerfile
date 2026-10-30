FROM python:3.13-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
COPY requirements-prod.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements-prod.txt

FROM python:3.13-slim
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY . .
RUN chmod +x /app/docker-entrypoint.sh
USER 65532:65532
EXPOSE 5000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
