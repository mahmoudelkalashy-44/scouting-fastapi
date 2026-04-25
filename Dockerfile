FROM python:3.10.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies with relaxed constraints
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
    "fastapi>=0.100.0,<0.105.0" \
    "uvicorn[standard]>=0.23.0" \
    "pydantic>=2.4.0,<2.6.0" \
    "pydantic-settings>=2.0.0" \
    "pandas>=2.0.0" \
    "numpy>=1.24.0,<1.25.0" \
    "scikit-learn>=1.3.0" \
    "tensorflow-cpu==2.13.0" \
    "keras==2.13.1" \
    "h5py==3.9.0" \
    "protobuf==3.20.3" \
    "joblib>=1.3.0" \
    "xgboost>=1.7.0" \
    "python-dotenv>=1.0.0" \
    "unidecode>=1.3.0" \
    "rapidfuzz>=3.5.0" \
    "groq>=0.4.0" \
    "requests>=2.31.0" \
    "pyarrow>=14.0.0" \
    "typing-extensions>=4.5.0,<4.7.0"

# Copy the rest of the application
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]