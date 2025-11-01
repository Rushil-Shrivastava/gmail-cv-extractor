# ======================
# Gmail CV Extractor Dockerfile
# ======================
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app ./app
COPY data ./data
COPY attachments ./attachments

# Expose port (for FastAPI if needed)
EXPOSE 8000

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    ATTACHMENTS_DIR=/app/attachments \
    DATABASE_URL=sqlite:///./data/cv_database.db

# Default command (runs sync)
CMD ["python", "-m", "app.run_sync"]