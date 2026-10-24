FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY counterfoil counterfoil
COPY scripts scripts
COPY docs/senaryolar docs/senaryolar
COPY astropods/run.sh astropods/run.env astropods/
RUN adduser --disabled-password --uid 1000 agent && mkdir -p results && chown agent results
USER agent
CMD ["sh", "astropods/run.sh"]
