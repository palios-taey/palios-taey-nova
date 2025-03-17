FROM python:3.10
WORKDIR /app
COPY ./src /app/src
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH=/app
CMD ["gunicorn", "--chdir", "/app/src", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "main:app"]