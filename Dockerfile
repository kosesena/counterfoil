# Counterfoil live demo. Keys come from the platform's environment at run time, never from the image.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd --create-home demo
USER demo

EXPOSE 8000
# --proxy-headers: behind Render's or Caddy's proxy the per-IP limit must see the visitor, not the proxy
CMD ["sh", "-c", "exec uvicorn demo.app:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
