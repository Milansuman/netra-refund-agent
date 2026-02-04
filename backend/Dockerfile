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

# Run in production mode with uvicorn
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
