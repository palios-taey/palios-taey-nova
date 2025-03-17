FROM python:3.10
WORKDIR /app
COPY ./src /app/src
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "src.main:app"]