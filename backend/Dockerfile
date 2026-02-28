# Use a high-performance Python 3.12 base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install uv for high-speed dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the backend manifest and the source code
COPY pyproject.toml .
COPY main.py .
COPY src/ ./src/

# Install dependencies into the system environment
RUN uv pip install --system -r pyproject.toml

# Expose the port App Runner will listen on
EXPOSE 8000

# Start the Warden Engine
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
