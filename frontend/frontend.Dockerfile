FROM python:3.10-slim

WORKDIR /app

COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common ./common
COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "frontend/app3.py", "--server.port=8501", "--server.address=0.0.0.0"]
