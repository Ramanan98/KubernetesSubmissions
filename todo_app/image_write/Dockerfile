FROM --platform=linux/amd64 python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir requests
COPY app.py .
CMD ["python", "app.py"]