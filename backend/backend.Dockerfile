FROM python:3.10-slim

WORKDIR /app

# Install minimal system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install pip & wheel first (faster installs)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

COPY . .

RUN python knowledge_base/atlan_info.py

EXPOSE 8000
CMD ["python", "main_mcp_server.py"]
