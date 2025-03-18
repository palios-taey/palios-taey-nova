FROM python:3.9-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project structure
COPY src/ /app/src/
COPY config/ /app/config/
COPY *.py .
COPY templates/ templates/

# Set environment variables
ENV PORT=8080
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8080

# Command to run the application
CMD ["python", "app.py"]
