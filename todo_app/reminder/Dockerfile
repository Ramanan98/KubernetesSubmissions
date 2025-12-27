FROM --platform=linux/amd64 python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir requests
RUN pip install psycopg2-binary
COPY app.py .
CMD ["python", "app.py"]