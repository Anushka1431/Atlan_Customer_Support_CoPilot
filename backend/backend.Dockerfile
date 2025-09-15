FROM python:3.10-slim

WORKDIR /app

# Install system deps if needed (e.g., ffmpeg, git)
RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python knowledge_base/atlan_info.py

EXPOSE 8000
CMD ["python", "main_mcp_server.py"]
