FROM python:3.12-slim

WORKDIR /app

# Install uv for faster dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./
# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Copy application code
COPY . .

# Expose the port
EXPOSE 8000

# Create startup script to run migrations then start server
RUN echo '#!/bin/sh\nfastapi run main.py --host 0.0.0.0 --port 8000' > /app/start.sh && \
    chmod +x /app/start.sh

# Run in production mode with uvicorn
CMD ["/app/start.sh"]
