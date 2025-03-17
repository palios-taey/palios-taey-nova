FROM python:3.10-slim

WORKDIR /app

# Create directories
RUN mkdir -p logs

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV USE_MOCK_RESPONSES=true

# Expose the port
EXPOSE 8080

# Start the application with gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 'src.main:app'
