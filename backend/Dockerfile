FROM python:3.11-slim

WORKDIR /app

# System dependencies for psycopg2, weasyprint, cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libssl-dev libmagic1 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the whole backend
COPY . .

# Create uploads/exports dirs
RUN mkdir -p /app/uploads /app/exports /tmp/exports

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
