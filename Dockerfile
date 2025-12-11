FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for weasyprint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfribidi0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create database directory if it doesn't exist
RUN mkdir -p /app/database

# Expose port for potential web interface (future)
EXPOSE 8000

# Default command: run the chatbot
# Default command: run the chatbot
CMD ["python", "HuizenManager/src/chat.py"]
