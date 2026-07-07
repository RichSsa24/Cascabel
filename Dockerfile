FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY cascabel/ cascabel/
COPY data/ data/
COPY frontend/dist/ frontend/dist/

# Set env
ENV PYTHONPATH=/app
ENV CASCABEL_API_HOST=0.0.0.0
ENV CASCABEL_AGENT_HOST=target-linux

# Start FastAPI server
CMD ["python", "-m", "cascabel.cli", "serve"]
