FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY frontend/requirements.txt .
COPY protobufs/ /app/protobufs/
COPY dictionary_service/ /app/dictionary_service/

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m grpc_tools.protoc -I /app/protobufs \
    --python_out=/app \
    --grpc_python_out=/app \
    /app/protobufs/dictionary.proto

COPY frontend/ /app/

RUN mkdir -p /app/templates

EXPOSE 8080

CMD ["python", "app.py"]