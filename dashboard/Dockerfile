FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard/ /app/dashboard/
COPY .env.example /app/.env.example

ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/main.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
