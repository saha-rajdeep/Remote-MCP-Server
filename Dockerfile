# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY server.py .

# Expose the port the app runs on
EXPOSE 8000

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash mcpuser
USER mcpuser

# Run the server
CMD ["python", "server.py"]
