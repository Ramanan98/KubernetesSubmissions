FROM --platform=linux/amd64 python:3.13-slim
WORKDIR /app
COPY app.py .
RUN pip install psycopg2-binary
CMD ["python", "app.py"]