FROM python:3.9-slim

WORKDIR /usr/src/app

ENV PYTHONPATH=/usr/src/app

RUN apt-get update && \
    apt-get install -y gcc libpq-dev netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /usr/src/app/wait-for-kafka.sh

ENV KAFKA_BOOTSTRAP_SERVERS=kafka

CMD ["./wait-for-kafka.sh", "bash", "-c", "uvicorn main:app --host 0.0.0.0 --port 80"]


